"""Focused output-contract regressions for bounded workflow artifacts."""
from contextlib import contextmanager
import json
import sqlite3

import pytest
from pydantic import ValidationError

from app.workflow_contracts import ARTIFACT_SCHEMAS
from app.workflows import WorkflowEngine


HASH = 'a' * 64
REASON = 'Latest registered file identity checked; document content was not verified.'


def citation_payload(version_rows):
    return {
        'schema_version': 'citation_batch_v1',
        'full_input_sha256': HASH,
        'source_input_sha256': HASH,
        'checks': [],
        'evidence_version_checks': version_rows,
        'issues': [],
    }


@pytest.mark.parametrize(('row', 'expected_status'), [
    ({'evidence_id': 7, 'file_id': 21, 'file_sha256': HASH, 'status': 'current', 'reason': REASON}, 'current'),
    ({'evidence_id': 8, 'file_id': None, 'file_sha256': None, 'status': 'current', 'reason': REASON}, 'current'),
    # The referenced file is an older registered version; the check records
    # that the latest version changed without claiming content was reviewed.
    ({'evidence_id': 9, 'file_id': 31, 'file_sha256': 'b' * 64, 'status': 'evidence_changed', 'reason': REASON}, 'evidence_changed'),
])
def test_citation_artifact_accepts_typed_evidence_version_rows(row, expected_status):
    artifact = ARTIFACT_SCHEMAS['CITATION_CHECKS'].model_validate(
        citation_payload([row])
    )

    serialized = artifact.model_dump()
    checked = serialized['evidence_version_checks'][0]
    assert checked['schema_version'] == 'evidence_version_check_v1'
    assert checked['status'] == expected_status
    assert checked['content_verified'] is False


def test_evidence_version_check_cannot_claim_content_verification():
    with pytest.raises(ValidationError):
        ARTIFACT_SCHEMAS['CITATION_CHECKS'].model_validate(citation_payload([{
            'evidence_id': 7, 'file_id': 21, 'file_sha256': HASH,
            'status': 'current', 'content_verified': True, 'reason': REASON,
        }]))


def test_citation_compute_publishes_current_missing_and_replaced_file_rows():
    database = sqlite3.connect(':memory:')
    database.row_factory = sqlite3.Row
    database.executescript('''
        CREATE TABLE sources(id INTEGER, tender_id INTEGER, sha256 TEXT, bytes INTEGER, pages INTEGER);
        CREATE TABLE evidence(id INTEGER, organization_id INTEGER);
        CREATE TABLE evidence_files(id INTEGER, evidence_id INTEGER, sha256 TEXT);
    ''')
    database.execute('INSERT INTO sources VALUES(2,4,?,80,1)', (HASH,))
    database.executemany('INSERT INTO evidence VALUES(?,12)', [(11,), (12,), (13,)])
    database.execute('INSERT INTO evidence_files VALUES(110,11,?)', (HASH,))
    database.executemany('INSERT INTO evidence_files VALUES(?,?,?)', [
        (130, 13, 'b' * 64), (131, 13, 'c' * 64),
    ])

    class PdfPage:
        def extract_text(self):
            return 'Minimum experience must include five years of work.'

    class Pdf:
        pages = [PdfPage()]

    class Domain:
        HOSTED = False

        @contextmanager
        def conn(self):
            yield database

        def read_registered_pdf(self, _source):
            return Pdf()

        def checked_pdf(self, _data):
            return Pdf()

    target_key = 'requirement:5'
    suggestions = [
        {'requirement_or_candidate_key': target_key, 'evidence_id': 11,
         'file_id': 110, 'file_sha256': HASH},
        {'requirement_or_candidate_key': target_key, 'evidence_id': 12,
         'file_id': None, 'file_sha256': None},
        {'requirement_or_candidate_key': target_key, 'evidence_id': 13,
         'file_id': 130, 'file_sha256': 'b' * 64},
    ]
    manifest = {
        'source_input_sha256': HASH,
        'source_scope': {'sources': [{'id': 2, 'sha256': HASH, 'bytes': 80, 'pages': 1}]},
        'requirements': [{'id': 5, 'text': 'Minimum experience', 'source_id': 2,
                          'source_page': 1, 'source_quote': 'Minimum experience must include five years of work.'}],
        'as_of_date': '2026-10-10', 'evidence': [],
    }
    claim = {
        'job': {'tender_id': 4, 'organization_id': 12, 'input_manifest': json.dumps(manifest),
                'input_sha256': 'd' * 64},
        'step': {'task_kind': 'CITATION_CHECK', 'cursor_json': '{"index":0}'},
        'artifacts': [{'artifact_kind': 'EVIDENCE_SUGGESTIONS',
                       'payload_json': json.dumps({'suggestions': suggestions})}],
    }

    try:
        kind, payload, next_index, complete = WorkflowEngine(Domain()).compute(claim)
        artifact = ARTIFACT_SCHEMAS[kind].model_validate(payload).model_dump()
        by_evidence = {row['evidence_id']: row for row in artifact['evidence_version_checks']}
        assert next_index == 1 and complete is True
        assert {evidence: row['status'] for evidence, row in by_evidence.items()} == {
            11: 'current', 12: 'current', 13: 'evidence_changed',
        }
        assert all(row['content_verified'] is False for row in by_evidence.values())
    finally:
        database.close()


@pytest.mark.parametrize('row', [
    {'evidence_id': 7, 'file_id': None, 'file_sha256': HASH, 'status': 'current', 'reason': REASON},
    {'evidence_id': 7, 'file_id': 21, 'file_sha256': None, 'status': 'current', 'reason': REASON},
    {'evidence_id': 7, 'file_id': 21, 'file_sha256': HASH, 'status': 'other', 'reason': REASON},
    {'evidence_id': 7, 'file_id': 21, 'file_sha256': HASH, 'status': 'current', 'reason': REASON, 'private_path': '/tmp/private.pdf'},
])
def test_evidence_version_check_rejects_inconsistent_or_unbounded_rows(row):
    with pytest.raises(ValidationError):
        ARTIFACT_SCHEMAS['CITATION_CHECKS'].model_validate(citation_payload([row]))
