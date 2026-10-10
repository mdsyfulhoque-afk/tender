"""A bounded current evidence library must not hide frozen run history."""
import hashlib
import io
import sqlite3
import uuid

from app import main
from app.commercial_schema import initialize_local_commercial
from app.database import initialize_local_extensions
from app.workflow_schema import initialize_local_workflows
from app.workflow_contracts import LIMITS, canonical
from app.workflows import WorkflowEngine
from pypdf import PdfReader
from test_workflows import synthetic_pdf


def test_frozen_workflow_history_remains_readable_above_current_evidence_limit(tmp_path, monkeypatch):
    database = tmp_path / 'currency-bound.sqlite3'
    storage = tmp_path / 'private-files'
    storage.mkdir()
    monkeypatch.setattr(main, 'DB', database)
    monkeypatch.setattr(main, 'STORAGE', storage)
    with sqlite3.connect(database) as cx:
        cx.executescript(main.SCHEMA)
        initialize_local_extensions(cx)
        initialize_local_workflows(cx)
        initialize_local_commercial(cx)

    pdf_bytes = synthetic_pdf(
        ('Synthetic administrative cover page.',),
        ('Three completed projects are documented.',),
    )
    private_key = uuid.uuid4().hex + '.pdf'
    (storage / private_key).write_bytes(pdf_bytes)
    source_hash = hashlib.sha256(pdf_bytes).hexdigest()
    with main.conn() as db:
        org_cursor = db.execute('INSERT INTO organizations(name,created_at) VALUES(?,?)',
                                ('Currency Bound Test Ltd', main.now()))
        org = org_cursor.lastrowid
        tender_cursor = db.execute('INSERT INTO tenders(organization_id,title,created_at) VALUES(?,?,?)',
                                   (org, 'One source workflow currency test', main.now()))
        tender = tender_cursor.lastrowid
        source_cursor = db.execute('''INSERT INTO sources(tender_id,name,sha256,bytes,private_path,pages,uploaded_at)
            VALUES(?,?,?,?,?,?,?)''',
            (tender, 'requirements.pdf', source_hash, len(pdf_bytes), private_key, 2, main.now()))
        source = source_cursor.lastrowid
        db.execute('''INSERT INTO tender_inventory_items(tender_id,title,document_type,publication_date,language,
            version_label,supersedes_item_id,source_id,availability,notes,created_at,updated_at)
            VALUES(?,?,?,NULL,?,?,NULL,?,'AVAILABLE','',?,?)''',
            (tender, 'Synthetic source PDF', 'RFP', 'English', 'Original', source, main.now(), main.now()))

    engine = WorkflowEngine(main)
    created = engine.create(tender, 'currency-bound-run-0001', {'processor_kind': 'RULES'})
    job = created['id']
    for _ in range(16):
        run = engine.advance(tender, job)
        if run['state'] == 'WAITING_HUMAN':
            break
    else:
        raise AssertionError('The one-source rules run did not reach its human review gate')

    original = engine.detail(tender, job)
    assert len(original['artifacts']) == 5
    original_hashes = [(item['id'], item['output_sha256']) for item in original['artifacts']]

    # Mirror the supported evidence registration fields. These are ordinary,
    # unverified records without files and make no document-validity claims.
    with main.conn() as db:
        db.executemany('''INSERT INTO evidence(organization_id,label,reference,expires_on,verified,
            verification_note,created_at) VALUES(?,?,?,NULL,0,'',?)''',
            [(org, f'Bounded evidence {index}', f'BOUND-{index:03d}', main.now())
             for index in range(501)])

    listed = engine.list(tender)
    assert len(listed) == 1
    listing_currency = listed[0]['currency']
    assert listing_currency['full_current'] is False
    assert listing_currency['source_current'] is True
    assert listing_currency['full_current_reason'] == 'BOUNDED_CURRENT_INPUT'
    assert 'organization evidence (501/500)' in listing_currency['reason_detail']

    detail = engine.detail(tender, job)
    assert detail['state'] == 'STALE'
    assert detail['currency']['full_current'] is False
    assert detail['currency']['source_current'] is True
    assert detail['currency']['full_current_reason'] == 'BOUNDED_CURRENT_INPUT'
    assert [(item['id'], item['output_sha256']) for item in detail['artifacts']] == original_hashes

    exported = engine.receipt(tender, job)
    assert exported['currency_at_export']['full_current'] is False
    assert exported['currency_at_export']['source_current'] is True
    assert exported['currency_at_export']['full_current_reason'] == 'BOUNDED_CURRENT_INPUT'
    assert exported['receipt']['state_at_capture'] == 'STALE'
    assert len(exported['receipt']['artifacts']) == 4


def test_source_inspect_omits_text_when_canonical_page_record_exceeds_limit(tmp_path, monkeypatch):
    database = tmp_path / 'escaped-page.sqlite3'
    storage = tmp_path / 'private-files'
    storage.mkdir()
    monkeypatch.setattr(main, 'DB', database)
    monkeypatch.setattr(main, 'STORAGE', storage)
    with sqlite3.connect(database) as cx:
        cx.executescript(main.SCHEMA)
        initialize_local_extensions(cx)
        initialize_local_workflows(cx)
        initialize_local_commercial(cx)

    raw_text = 'certificate ' + '\x00' * 18000
    pdf_bytes = synthetic_pdf((raw_text,))
    extracted = PdfReader(io.BytesIO(pdf_bytes), strict=True).pages[0].extract_text() or ''
    assert len(extracted) == 18013
    private_key = uuid.uuid4().hex + '.pdf'
    (storage / private_key).write_bytes(pdf_bytes)
    source_hash = hashlib.sha256(pdf_bytes).hexdigest()
    with main.conn() as db:
        org = db.execute('INSERT INTO organizations(name,created_at) VALUES(?,?)',
                         ('Canonical Page Bound Ltd', main.now())).lastrowid
        tender = db.execute('INSERT INTO tenders(organization_id,title,created_at) VALUES(?,?,?)',
                            (org, 'Canonical page payload limit', main.now())).lastrowid
        source = db.execute('''INSERT INTO sources(tender_id,name,sha256,bytes,private_path,pages,uploaded_at)
            VALUES(?,?,?,?,?,?,?)''',
            (tender, 'nul-heavy.pdf', source_hash, len(pdf_bytes), private_key, 1, main.now())).lastrowid
        db.execute('''INSERT INTO tender_inventory_items(tender_id,title,document_type,publication_date,language,
            version_label,supersedes_item_id,source_id,availability,notes,created_at,updated_at)
            VALUES(?,?,?,NULL,?,?,NULL,?,'AVAILABLE','',?,?)''',
            (tender, 'NUL-heavy source PDF', 'RFP', 'English', 'Original', source, main.now(), main.now()))

    raw_record = {'source_id': source, 'source_sha256': source_hash, 'page': 1, 'text': extracted,
                  'text_sha256': hashlib.sha256(extracted.encode('utf-8')).hexdigest(),
                  'character_count': len(extracted), 'coverage_status': 'TEXT_READY'}
    assert len(canonical(raw_record).encode('utf-8')) > LIMITS['max_page_payload_bytes']

    engine = WorkflowEngine(main)
    job = engine.create(tender, 'escaped-page-run-0001', {'processor_kind': 'RULES'})['id']
    inspected = engine.advance(tender, job)
    source_batch = next(a for a in inspected['artifacts'] if a['artifact_kind'] == 'SOURCE_BATCH')['payload']
    page = source_batch['pages'][0]
    assert page['coverage_status'] == 'INCOMPLETE_BOUND'
    assert page['text'] == ''
    assert page['character_count'] == len(extracted)
    assert page['text_sha256'] == hashlib.sha256(b'').hexdigest()
    assert len(canonical(page).encode('utf-8')) <= LIMITS['max_page_payload_bytes']
    assert len(canonical(source_batch).encode('utf-8')) <= LIMITS['max_artifact_bytes']
    assert any(issue['code'] == 'INCOMPLETE_BOUND' and issue['source_id'] == source and issue['page'] == 1
               and 'Canonical page record exceeds the per-page payload limit' in issue['message']
               for issue in source_batch['issues'])
