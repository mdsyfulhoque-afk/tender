"""Independent bounded QA using only imported source and synthetic data.

Application source is read-only. All runtime state stays outside the repository.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from zipfile import ZipFile


REPO = Path('/workspace/tender/TenderOS')
RUNTIME = Path('/workspace/tenderos-audit-runtime')
OUTPUT = REPO / 'verification/current-baseline'
ARCHIVE = Path('/tmp/codex-remote-attachments/01a12138-29be-72ba-9771-158f618a304b/25b815ab-3db0-4592-a607-5c40b901100f/2-TenderOS_Codex_Work_Transfer_v1_2.zip')
PREFIX = 'TenderOS_Codex_Work_Transfer_v1_2/'


def utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, value):
    path = OUTPUT / name
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return path


def run():
    started = utc()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    import_report = json.loads((REPO / 'verification/IMPORT_REPORT.json').read_text())
    preservation = []
    with ZipFile(ARCHIVE) as archive:
        for item in import_report['source_destination_map']:
            original = archive.read(item['archive_path'])
            local = Path(item['destination_path']).read_bytes()
            preservation.append({
                'archive_path': item['archive_path'],
                'destination_relative_path': item['destination_relative_path'],
                'sha256': sha(local),
                'byte_identical_to_archive': original == local,
            })
    assert len(preservation) == 30 and all(x['byte_identical_to_archive'] for x in preservation)
    assert not (REPO / 'data/tenderos.sqlite3').exists(), 'Excluded archive DB present in repository'
    active_governance_sha = sha((REPO / 'AGENTS.md').read_bytes())
    assert active_governance_sha == '1fbca1e2b3c5be11438c39aa7e4b2ab7f02554e62dfd1ed1a3f9f670cdfa3ef6'
    source_hashes = {p: sha((REPO / p).read_bytes()) for p in (
        'AGENTS.md', 'app/main.py', 'app/static/index.html', 'app/static/style.css',
        'app/static/ui.js', 'tests/conftest.py', 'tests/test_workflows.py', 'requirements.txt'
    )}
    expected_tests = [
        'test_mandatory_blocker_and_human_gate',
        'test_fail_closed_when_unreviewed',
        'test_no_verified_without_current_evidence',
        'test_cross_organization_evidence_rejected',
        'test_exports_and_metrics',
        'test_pdf_has_source_provenance',
        'test_health_and_demo',
        'test_missing_provenance_keeps_mandatory_unresolved',
        'test_changed_requirements_invalidate_prior_bid',
        'test_excel_formula_injection_blocked',
    ]
    test_tree = ast.parse((REPO / 'tests/test_workflows.py').read_text())
    actual_tests = [node.name for node in test_tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
    assert actual_tests == expected_tests
    save('source-preservation.json', {
        'archive_sha256': sha(ARCHIVE.read_bytes()),
        'checked_mapped_files': preservation,
        'active_governance_sha256': active_governance_sha,
        'source_hashes': source_hashes,
        'expected_test_names': expected_tests,
        'test_names_match': True,
        'excluded_archive_database_present': False,
    })
    packages = ('fastapi','uvicorn','python-multipart','pypdf','python-docx','openpyxl','pytest','httpx','reportlab','pydantic','starlette')
    versions = {name: importlib.metadata.version(name) for name in packages}
    save('resolved-dependencies.json', {'python': sys.version, 'executable': sys.executable, 'versions': versions})

    command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               '--basetemp=' + str(RUNTIME / 'baseline-tmp')]
    env = os.environ.copy()
    env.update({'TENDEROS_DATA_DIR': str(RUNTIME / 'baseline-import-data'),
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'})
    baseline_started = utc()
    baseline = subprocess.run(command, cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    (OUTPUT / 'baseline.stdout.txt').write_text(baseline.stdout)
    (OUTPUT / 'baseline.stderr.txt').write_text(baseline.stderr)
    baseline_ok = baseline.returncode == 0 and bool(re.search(r'\b10 passed\b', baseline.stdout)) and not re.search(r'\b\d+ (skipped|failed|error)', baseline.stdout)
    baseline_result = {
        'command_argv': command, 'cwd': str(REPO),
        'environment_overrides': {k: env[k] for k in ('TENDEROS_DATA_DIR','PYTHONDONTWRITEBYTECODE','PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
        'start_utc': baseline_started, 'end_utc': utc(), 'exit_code': baseline.returncode,
        'passed': 10 if baseline_ok else None, 'skipped': 0 if baseline_ok else None,
        'failed': 0 if baseline_ok else None, 'all_ten_tests_executed': baseline_ok,
    }
    save('baseline-result.json', baseline_result)
    assert baseline_ok, 'Baseline did not execute all original ten tests successfully; see captured output'

    # Set external data path before importing the application: import creates DB/storage.
    os.environ['TENDEROS_DATA_DIR'] = str(RUNTIME / 'independent-reproduction-data')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.path.insert(0, str(REPO))
    from fastapi.testclient import TestClient
    from app import main
    from reportlab.pdfgen.canvas import Canvas
    from openpyxl import load_workbook

    assert main.DB.parent == RUNTIME / 'independent-reproduction-data'
    request_log = []

    def request(client, method, path, expected, **kwargs):
        response = getattr(client, method)(path, **kwargs)
        request_log.append({'method': method.upper(), 'path': path, 'expected': expected, 'actual': response.status_code})
        assert response.status_code == expected, (method, path, response.status_code, response.text[:300])
        return response

    def stored_decisions(tender):
        with sqlite3.connect(main.DB) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM decisions WHERE tender_id=? ORDER BY id', (tender,))]

    def state(snap):
        return {key: snap[key] for key in ('compliance','current_decision','source_scope_verified','source_scope_fingerprint','fingerprint','decisions')}

    def create_ready(client, title='Independent synthetic QA tender'):
        org = request(client,'post','/api/organizations',201,json={'name':'Independent Synthetic QA Organization'}).json()['id']
        tender = request(client,'post','/api/tenders',201,json={'organization_id':org,'title':title}).json()['id']
        text = 'Three synthetic projects must be documented'
        requirement = request(client,'post',f'/api/tenders/{tender}/requirements',201,json={'text':text,'source_page':1,'source_quote':text}).json()['id']
        request(client,'put',f'/api/requirements/{requirement}/review',200,json={'text':text,'mandatory':True,'source_page':1,'source_quote':text})
        evidence = request(client,'post','/api/evidence',201,json={'organization_id':org,'label':'Synthetic signed certificate','reference':'SYNTHETIC-QA-001','verified':True,'verification_note':'Synthetic test-only evidence'}).json()['id']
        request(client,'put',f'/api/requirements/{requirement}/status',200,json={'status':'VERIFIED','evidence_id':evidence,'notes':'Synthetic verified evidence'})
        request(client,'post',f'/api/tenders/{tender}/attest-source-scope',200,json={'reviewer':'Synthetic QA Reviewer','note':'Reviewed complete synthetic source set and all test-only amendments','checked_full_document_set':True})
        return tender

    with TestClient(main.app) as client:
        startup = {}
        for path in ('/api/health','/','/api/docs'):
            response = request(client,'get',path,200)
            startup[path] = {'status_code':response.status_code,'content_type':response.headers.get('content-type'),'body_sha256':sha(response.content)}
            if path == '/api/health':
                startup[path]['json'] = response.json()
                assert response.json() == {'status':'ok','mode':'LOCAL_PILOT','external_model_calls':False}
            elif path == '/': assert 'TenderOS' in response.text
            elif path == '/api/docs': assert 'swagger' in response.text.lower()
        save('startup-checks.json', startup)

        tender = create_ready(client)
        decision_payload = {'decision':'BID','reviewer':'Synthetic QA Reviewer','rationale':'Approved only against complete synthetic test evidence and source inventory'}
        request(client,'post',f'/api/tenders/{tender}/decisions',201,json=decision_payload)
        before = request(client,'get',f'/api/tenders/{tender}',200).json()
        rows_before = stored_decisions(tender)
        assert before['compliance'] == 'READY_FOR_HUMAN_DECISION'
        assert before['current_decision'] == 'BID' and before['source_scope_verified'] is True

        pdf_buffer = io.BytesIO()
        canvas = Canvas(pdf_buffer)
        canvas.drawString(50,750,'Calendar update: delivery date 2030-01-15.')
        canvas.showPage(); canvas.save()
        pdf = pdf_buffer.getvalue()
        upload = request(client,'post',f'/api/tenders/{tender}/upload-pdf',201,
                         files={'file':('synthetic-addendum.pdf',pdf,'application/pdf')}).json()
        assert upload['candidates'] == 0
        after = request(client,'get',f'/api/tenders/{tender}',200).json()
        rows_after = stored_decisions(tender)
        rejected_bid = request(client,'post',f'/api/tenders/{tender}/decisions',409,json=decision_payload)
        rows_after_reject = stored_decisions(tender)
        defect_reproduced = after['compliance'] == 'UNRESOLVED' and after['current_decision'] == 'BID' and after['decisions'][0]['is_current'] is True and after['source_scope_verified'] is False
        assert rows_before == rows_after == rows_after_reject, 'Decision storage changed unexpectedly'
        assert before['fingerprint'] == after['fingerprint']
        assert before['source_scope_fingerprint'] != after['source_scope_fingerprint']
        assert len(after['requirements']) == len(before['requirements'])
        reproduction = {
            'defect_id':'DEF-001', 'data':'synthetic only',
            'before':state(before), 'after_zero_candidate_addendum':state(after),
            'pdf_upload_response':upload, 'pdf_sha256':sha(pdf),
            'new_bid_status':rejected_bid.status_code,'new_bid_response':rejected_bid.json(),
            'requirements_count_before':len(before['requirements']), 'requirements_count_after':len(after['requirements']),
            'source_count_before':len(before['sources']), 'source_count_after':len(after['sources']),
            'stored_decision_rows_before':rows_before, 'stored_decision_rows_after':rows_after,
            'stored_decision_rows_after_rejected_bid':rows_after_reject,
            'stored_history_byte_content_preserved':rows_before == rows_after == rows_after_reject,
            'stored_history_sha256_before':sha(json.dumps(rows_before,sort_keys=True).encode()),
            'stored_history_sha256_after':sha(json.dumps(rows_after,sort_keys=True).encode()),
            'observed_defect_reproduced':defect_reproduced,
            'expected_safe_current_decision':None,
            'safety_expectation_passed':not defect_reproduced,
            'note':'Original baseline passed; separate safety reproduction demonstrates unresolved defect without modifying app.'
        }
        save('DEF-001-reproduction.json',reproduction)
        assert defect_reproduced, 'Documented DEF-001 did not reproduce'

        # Benign spreadsheet formula strings: no workbook formula calculation performed.
        formula_tender = create_ready(client,title='=1+1')
        formula_rationale = '=1+1       ' # Meets API raw minimum length; strip() stores the benign formula.
        request(client,'post',f'/api/tenders/{formula_tender}/decisions',201,json={
            'decision':'BID','reviewer':'=1+1','rationale':formula_rationale})
        workbook_response = request(client,'get',f'/api/tenders/{formula_tender}/export.xlsx',200)
        workbook = load_workbook(io.BytesIO(workbook_response.content))
        cells = []
        for sheet,coordinate,field in (('Compliance Matrix','B2','tender.title'),('Decision History','B2','decision.reviewer'),('Decision History','C2','decision.rationale')):
            cell = workbook[sheet][coordinate]
            cells.append({'sheet':sheet,'cell':coordinate,'input_field':field,'value':cell.value,'data_type':cell.data_type,'interpreted_as_formula':cell.data_type == 'f'})
        save('XLSX-formula-observation.json',{
            'data':'synthetic only','benign_formula':'=1+1','workbook_sha256':sha(workbook_response.content),
            'formula_evaluated':False,'cells':cells,
            'all_three_fields_stored_as_formula':all(c['interpreted_as_formula'] for c in cells),
            'title_input_characters':4,'rationale_payload_uses_padding_to_satisfy_raw_min_length':True,
            'application_modified':False,
        })

    save('synthetic-request-log.json',request_log)
    after_hashes = {p:sha((REPO/p).read_bytes()) for p in source_hashes}
    assert after_hashes == source_hashes, 'Source changed during independent test execution'
    artifact_hashes = {str(p.relative_to(OUTPUT)):sha(p.read_bytes()) for p in OUTPUT.iterdir() if p.is_file() and p.name!='independent-receipt.json'}
    receipt = {
        'task_id':'T-002 independent baseline and synthetic regression reproduction',
        'canonical_agent_id':'/root/tenderos_independent_verification',
        'agent_runtime':'Codex delegated subagent; existing agent resumed by collaboration.followup_task',
        'opaque_run_id':None,'opaque_run_id_status':'No separate opaque run ID exposed; no ID invented.',
        'start_utc_first_tool_observation':'2026-10-09T15:44:50Z',
        'harness_start_utc':started,'end_utc':utc(),
        'branch':'tenderos/import-v1.2', 'read_write_scope':{
            'read_only_app_source':str(REPO),'synthetic_runtime_writes':str(RUNTIME),
            'verification_artifact_writes':str(OUTPUT)},
        'command':[sys.executable,str(Path(__file__))],
        'baseline':baseline_result,'startup_statuses':{p:v['status_code'] for p,v in startup.items()},
        'DEF001_reproduced':defect_reproduced,'immutable_stored_history_preserved':True,
        'xlsx_formula_cells':cells,'source_hashes_before':source_hashes,'source_hashes_after':after_hashes,
        'application_source_modified':False,'database_from_archive_read':False,
        'network_calls':False,'external_model_api_calls':False,'data':'synthetic only',
        'commit_push_merge_deploy':False,'artifact_hashes':artifact_hashes,
        'harness_sha256':sha(Path(__file__).read_bytes()),
        'tool_trace_preflight_chunks':['213dd8','43cf26','669f5f','02bc18','452945'],
        'current_execution_tool_chunk':'Execution response chunk ID becomes available after receipt is written; parent conversation preserves it.',
        'independent_reviewer_run_id':None,
        'open_risks':['DEF-001 reproduced','XLSX title/reviewer/rationale rendered as formula cells','opaque run ID unavailable'],
    }
    save('independent-receipt.json',receipt)
    print(json.dumps({'baseline':baseline_result,'startup':receipt['startup_statuses'],
                     'DEF001_reproduced':defect_reproduced,'history_preserved':True,
                     'XLSX_cells':cells,'source_unchanged':True,
                     'receipt_path':str(OUTPUT/'independent-receipt.json'),
                     'receipt_sha256':sha((OUTPUT/'independent-receipt.json').read_bytes())},indent=2))


if __name__ == '__main__':
    run()
