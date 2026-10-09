# TenderOS — Local Bid Decision Intelligence MVP

**State: locally runnable prototype, not production deployed or security-certified.**

TenderOS is a service-first pilot for Bangladesh consulting organizations evaluating tenders. It provides source-anchored requirements, human verification, evidence mapping, deterministic mandatory blockers, BID/NO-BID/HOLD sign-off, editable DOCX/XLSX/CSV outputs, audit records, and paid-pilot measurement. It neither submits bids nor calls an external AI provider.

## Start (Python 3.11+)

```bash
cd tenderos_mvp
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Optional Swagger API documentation: **http://127.0.0.1:8000/api/docs**.

**Run locally only.** Do not expose port 8000 publicly or upload confidential tender/company files to unapproved infrastructure. The local MVP has no authentication, secure multi-user permissions, encrypted database, or professional security review.

## Try it

1. Click **Load demonstration** to see completely synthetic records, including a mandatory blocker. Try approving `BID`: API rejects it.
2. Create your organization and opportunity. Enter a real tender title/reference, then import a text-based PDF or enter requirements manually.
3. Human-review the wording and classify each requirement as mandatory or optional.
4. Register **references** to evidence documents. Mark them verified only after checking the underlying document, recording what you checked.
5. Assign each requirement a status (VERIFIED, PARTIAL, NOT_HELD, UNKNOWN); VERIFIED requires linked unexpired and human-verified evidence.
6. **Attest completeness of the entire source document set** (including annexes and known amendments) after checking that no mandatory clauses were missed. New requirement/source changes revoke the attestation.
7. Record a named human **BID**, **NO-BID**, or **HOLD** decision. `BID` is rejected while mandatory compliance or complete-source attestation remains blocked/unresolved.
8. Download editable Word, Excel, or CSV matrices and record whether the pilot was **actually paid**.

### PDF specifics
- Local `pypdf` extracts text and rough candidate lines with page provenance.
- Extracted lines are unreviewed and have **no mandatory classification**, so they cannot silently count as compliant.
- Scanned images / complex tables may require manual transcription; there is no OCR.
- A SHA-256 hash identifies the privately stored original PDF. Files are kept in `data/private_uploads` and never served publicly.
- File limits: **10 MB**, **150 pages**, encrypted files rejected.
- Verify exact source interpretation yourself; heuristics can miss or mis-split a clause.

## Test

```bash
pytest -q
```

## Data location and backups

The local SQLite database is `data/tenderos.sqlite3`, with PDF originals under `data/private_uploads/`. Override the base directory via `TENDEROS_DATA_DIR=/private/location` before startup. Backup the whole data directory, and restrict operating-system file permissions. Avoid committing `data/` to source control. Delete synthetic client data when no longer required.

## Safety rules in code

- No model calls or web scraping; confidentiality stays local.
- Mandatory `NOT_HELD` is a blocker; `UNKNOWN`, `PARTIAL`, unreviewed, absent or expired proof stops BID.
- All requirements need human review and an explicit mandatory classification; mandatory requirements must have source provenance.
- BID additionally requires explicit human confirmation that the complete source inventory (including annexes and amendments) was reviewed.
- Evidence marked VERIFIED requires a verification note; the record is a human assertion, not machine authentication.
- BID only permitted after `READY_FOR_HUMAN_DECISION` state and a named human rationale.
- Decision records are append-only through the exposed API, while a local machine owner can still modify SQLite directly.
- Evidence cannot be mapped across organizations via the API; this **is not** production tenant isolation.
- Source PDF cannot be retrieved through public routes; exports contain requirement excerpts and notes.
- CSV formula-injection protection is enabled; XLSX is written as literal values using openpyxl.

## Production transition

See `docs/COMPANY_BLUEPRINT.md` for commercial validation, agent organization, governance, schema migration, security backlog, estimated cost model, launch gates and implementation roadmap.

In production, add OIDC/SSO authentication, server-enforced tenant/role authorization, explicit evidence-vault encryption, secure upload scanning, malware sandboxing, retention/deletion, reverse proxy/HTTPS, security monitoring, background worker queue, Postgres row-level security tests, CSRF defenses, strict egress limits, versioned agent evaluations, backup/restore drills and legal review before customer onboarding.
