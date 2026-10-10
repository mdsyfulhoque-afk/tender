"""Focused aggregate artifact-budget checks for final workflow receipts."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3

import pytest

from app import workflow_contracts
from app.workflow_schema import initialize_local_workflows
from app.workflow_contracts import canonical, digest, policy
from app.workflows import WorkflowEngine, timestamp


HASH = 'a' * 64
PAYLOAD = {
    'schema_version': 'citation_batch_v1',
    'full_input_sha256': HASH,
    'source_input_sha256': HASH,
    'checks': [],
    'evidence_version_checks': [],
    'issues': [],
}


class Domain:
    HOSTED = False

    def __init__(self, path):
        self.path = path

    @contextmanager
    def conn(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def require(db, table, row_id):
        assert table == 'tenders'
        row = db.execute('SELECT * FROM tenders WHERE id=?', (row_id,)).fetchone()
        assert row is not None
        return dict(row)


class CurrentInputsEngine(WorkflowEngine):
    def currency(self, db, job):
        return {'full_current': True, 'source_current': True}


def prepare_claim(tmp_path, monkeypatch):
    data_dir = tmp_path / 'tenderos-data'
    data_dir.mkdir()
    monkeypatch.setenv('TENDEROS_DATA_DIR', str(data_dir))
    path = data_dir / 'test.sqlite3'
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''
            CREATE TABLE tenders (
                id INTEGER PRIMARY KEY,
                organization_id INTEGER NOT NULL,
                UNIQUE(id,organization_id)
            );
            CREATE TABLE requirements (id INTEGER PRIMARY KEY, tender_id INTEGER NOT NULL);
        ''')
        initialize_local_workflows(db)
        db.execute('INSERT INTO tenders(id,organization_id) VALUES(1,7)')
        manifest = {
            'source_input_sha256': HASH,
            'source_scope': {'sources': []},
            'evidence': [],
        }
        frozen_policy = policy(False)
        now = timestamp()
        db.execute('''INSERT INTO workflow_jobs(
            id,tender_id,organization_id,workflow_kind,processor_kind,contract_version,state,
            created_by,idempotency_key,request_sha256,input_manifest,input_sha256,policy_manifest,
            policy_sha256,step_runs,elapsed_ms,revision,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (31, 1, 7, 'READINESS_REVIEW', 'RULES', 'tenderos_rules_review_v1', 'RUNNING',
             'SYSTEM:test', 'test-key-0123456789', HASH, canonical(manifest), HASH,
             canonical(frozen_policy), digest(frozen_policy), 1, 15000, 4, now, now))
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(timespec='milliseconds')
        db.execute('''INSERT INTO workflow_steps(
            id,job_id,task_kind,task_key,contract_version,executor_label,state,cursor_json,
            attempt_count,lease_owner,lease_expires_at,fence,input_sha256
        ) VALUES(41,31,'CITATION_CHECK','citation_check:v1','tenderos_rules_review_v1',
            'SYSTEM:local-rules','RUNNING','{"index":0}',1,'owner:test',?,2,?)''', (expiry, HASH))
        job = dict(db.execute('SELECT * FROM workflow_jobs WHERE id=31').fetchone())
        step = dict(db.execute('SELECT * FROM workflow_steps WHERE id=41').fetchone())
    return path, Domain(path), {'job': job, 'step': step}


def stored_artifact_size(db, job_id):
    return sum(len(row['payload_json'].encode('utf-8')) for row in db.execute(
        'SELECT payload_json FROM workflow_artifacts WHERE job_id=?', (job_id,)))


def test_final_receipt_and_citation_output_share_the_artifact_budget(tmp_path, monkeypatch):
    path, domain, claim = prepare_claim(tmp_path, monkeypatch)
    citation_bytes = len(canonical(PAYLOAD).encode('utf-8'))
    # The citation output fits by itself. The complete frozen receipt cannot.
    monkeypatch.setitem(workflow_contracts.LIMITS, 'max_artifact_bytes', citation_bytes + 1)

    published = CurrentInputsEngine(domain).publish(
        claim, ('CITATION_CHECKS', PAYLOAD, 0, True), elapsed=20, error=None)

    assert published is False
    with sqlite3.connect(path) as cx:
        cx.row_factory = sqlite3.Row
        job = dict(cx.execute('SELECT * FROM workflow_jobs WHERE id=31').fetchone())
        step = dict(cx.execute('SELECT * FROM workflow_steps WHERE id=41').fetchone())
        artifacts = [dict(row) for row in cx.execute(
            'SELECT * FROM workflow_artifacts WHERE job_id=31 ORDER BY id')]
        events = [dict(row) for row in cx.execute(
            "SELECT * FROM workflow_events WHERE job_id=31 AND action='BUDGET_EXHAUSTED'")]
        aggregate_bytes = stored_artifact_size(cx, 31)

    assert job['state'] == 'BUDGET_EXHAUSTED'
    assert job['last_error_code'] == 'ARTIFACT_LIMIT'
    assert job['elapsed_ms'] == 20
    assert step['state'] == 'FAILED'
    assert step['last_error_code'] == 'ARTIFACT_LIMIT'
    assert [artifact['artifact_kind'] for artifact in artifacts] == ['CITATION_CHECKS']
    assert aggregate_bytes == citation_bytes <= workflow_contracts.LIMITS['max_artifact_bytes']
    assert events and json.loads(events[0]['event_json'])['code'] == 'ARTIFACT_LIMIT'


def test_receipt_references_published_citation_and_reconciled_elapsed(tmp_path, monkeypatch):
    path, domain, claim = prepare_claim(tmp_path, monkeypatch)
    monkeypatch.setitem(workflow_contracts.LIMITS, 'max_artifact_bytes', 100_000)

    published = CurrentInputsEngine(domain).publish(
        claim, ('CITATION_CHECKS', PAYLOAD, 0, True), elapsed=23, error=None)

    assert published is True
    with sqlite3.connect(path) as cx:
        cx.row_factory = sqlite3.Row
        job = dict(cx.execute('SELECT * FROM workflow_jobs WHERE id=31').fetchone())
        step = dict(cx.execute('SELECT * FROM workflow_steps WHERE id=41').fetchone())
        artifacts = [dict(row) for row in cx.execute(
            'SELECT * FROM workflow_artifacts WHERE job_id=31 ORDER BY id')]
        aggregate_bytes = stored_artifact_size(cx, 31)

    assert job['state'] == 'WAITING_HUMAN'
    assert step['state'] == 'SUCCEEDED'
    assert [artifact['artifact_kind'] for artifact in artifacts] == ['CITATION_CHECKS', 'RUN_RECEIPT']
    receipt = json.loads(artifacts[-1]['payload_json'])
    assert [row['artifact_kind'] for row in receipt['artifacts']] == ['CITATION_CHECKS']
    assert receipt['usage']['elapsed_ms'] == 23
    assert aggregate_bytes <= workflow_contracts.LIMITS['max_artifact_bytes']
