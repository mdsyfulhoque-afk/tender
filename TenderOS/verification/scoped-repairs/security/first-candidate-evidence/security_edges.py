"""Additional boundary cases after immutable candidate review."""
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import date, timedelta
import argparse

import adversarial_review as h

SOURCE = Path('/workspace/tenderos-fix')
parser = argparse.ArgumentParser()
parser.add_argument('--commit', required=True)
args = parser.parse_args()
EXPECTED = args.commit
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == EXPECTED
os.environ['TENDEROS_DATA_DIR'] = str(h.HERE/'runtime'/'import-data')
sys.dont_write_bytecode = True
sys.path.insert(0,str(SOURCE/'TenderOS'))
h.MAIN = importlib.import_module('app.main')


def version_shape(value):
    f = h.Fixture().ready()
    raw = json.loads(f.sql('SELECT decision_snapshot FROM decisions')[0]['decision_snapshot'])
    raw['currency_version'] = value
    f.sql('UPDATE decisions SET decision_snapshot=?',(json.dumps(raw),))
    f.assert_stale(f.history())


def nested_attestation_omission(key):
    f = h.Fixture().ready()
    raw = json.loads(f.sql('SELECT decision_snapshot FROM decisions')[0]['decision_snapshot'])
    raw['scope_attestation'].pop(key)
    f.sql('UPDATE decisions SET decision_snapshot=?',(json.dumps(raw),))
    f.assert_stale(f.history())


def attestation_shape(kind):
    f = h.Fixture().ready()
    if kind == 'bool':
        # Create a legitimate attestation id=1 to expose Python's True == 1.
        # This is only an isolated synthetic DB state probe, not an API exploit.
        f.sql('DELETE FROM audit_events')
        f.attest()
        f.decide()
    latest = f.sql('SELECT id,decision_snapshot FROM decisions ORDER BY id DESC LIMIT 1')[0]
    raw = json.loads(latest['decision_snapshot'])
    nested = raw['scope_attestation']
    if kind == 'float':
        nested['event_id'] = float(nested['event_id'])
    elif kind == 'bool':
        assert nested['event_id'] == 1
        nested['event_id'] = True
    elif kind == 'missing':
        nested.pop('event_id')
    elif kind == 'extra':
        nested['unexpected'] = 'Synthetic extra metadata'
    elif kind == 'string_id':
        nested['event_id'] = str(nested['event_id'])
    elif kind == 'null_id':
        nested['event_id'] = None
    elif kind == 'list_id':
        nested['event_id'] = [nested['event_id']]
    elif kind == 'dict_id':
        nested['event_id'] = {'id': nested['event_id']}
    elif kind == 'null_attestation':
        raw['scope_attestation'] = None
    elif kind == 'list_attestation':
        raw['scope_attestation'] = list(nested.values())
    else:
        raise ValueError(kind)
    f.sql('UPDATE decisions SET decision_snapshot=? WHERE id=?',(json.dumps(raw),latest['id']))
    f.assert_stale(f.history())


def expiry_without_write():
    f = h.Fixture().ready()
    before = f.detail()
    expiry = date.fromisoformat(f.sql('SELECT expires_on FROM evidence WHERE id=?',(f.evidence,))[0]['expires_on'])
    original_date = h.MAIN.date
    history = f.history()
    class FutureDate(date):
        @classmethod
        def today(cls):
            return expiry+timedelta(days=1)
    h.MAIN.date = FutureDate
    try:
        after = f.assert_stale(history)
        assert after['compliance'] == 'UNRESOLVED'
        assert before['fingerprint'] != after['fingerprint']
        f.decide(expected=409)
        assert f.history() == history
    finally:
        h.MAIN.date = original_date


def provenance_change(field):
    f = h.Fixture().ready()
    history = f.history()
    f.sql(f'UPDATE tenders SET {field}=? WHERE id=?',('SYNTHETIC-CHANGED',f.tender))
    after = f.assert_stale(history)
    assert not after['source_scope_verified']


def non_bid(choice):
    f = h.Fixture().ready()
    f.sql('UPDATE tenders SET source_scope_fingerprint=NULL WHERE id=?',(f.tender,))
    f.decide(choice)
    snap = f.detail()
    assert snap['compliance'] == 'UNRESOLVED' and snap['current_decision'] == choice


for value in (True, 1.0, '1', None, 2):
    h.record(f'currency_version_rejects_type_or_value_{repr(value)}',lambda value=value:version_shape(value))
for key in ('event_id','reviewer','note','at','scope_hash'):
    h.record(f'missing_nested_attestation_{key}',lambda key=key:nested_attestation_omission(key))
for kind in ('float','bool','missing','extra','string_id','null_id','list_id','dict_id',
             'null_attestation','list_attestation'):
    h.record(f'malformed_attestation_shape_{kind}',lambda kind=kind:attestation_shape(kind))
h.record('linked_evidence_expires_without_any_db_write',expiry_without_write)
for field in ('notice_id','source_url'):
    h.record(f'tender_provenance_{field}_change',lambda field=field:provenance_change(field))
for choice in ('HOLD','NO_BID'):
    h.record(f'non_bid_current_when_unresolved_{choice}',lambda choice=choice:non_bid(choice))
for payload in ('#NULL!','#DIV/0!','#VALUE!','#REF!','#NAME?','#NUM!','#N/A',
                '#GETTING_DATA','#SPILL!','#CALC!','\ufeff=1+1 benign','\u200b=1+1 benign'):
    h.record(f'xlsx_text_edge_{repr(payload)}',lambda payload=payload:h.xlsx_literal_payload(payload))

report = {'task_id':'/root/tenderos_patch_security','source_commit':EXPECTED,
          'source_sha256':hashlib.sha256((SOURCE/'TenderOS/app/main.py').read_bytes()).hexdigest(),
          'runtime_run_id':None,'strict_historical_receipt_gate_passed':False,
          'data':'synthetic only','formula_evaluated':False,'external_model_calls':False,
          'cases':h.CASES,'passed':sum(c['passed'] for c in h.CASES),'failed':sum(not c['passed'] for c in h.CASES),
          'ended_at_utc':h.utc()}
(h.HERE/'security-edge-results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
(h.HERE/'synthetic-edge-request-trace.json').write_text(json.dumps(h.TRACE,indent=2)+'\n')
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip() == EXPECTED
print(json.dumps({'passed':report['passed'],'failed':report['failed'],
                  'failed_cases':[c for c in h.CASES if not c['passed']]}))
raise SystemExit(bool(report['failed']))
