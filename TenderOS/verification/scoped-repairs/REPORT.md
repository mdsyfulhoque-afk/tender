# TenderOS scoped repair verification — 2026-10-09

Status: verified for decision currency and literal spreadsheet exports. Final candidate `b8d99aa32abab9e46147eaac7ce93cdbb32307d4` passed separate QA and security review. This is a local pilot repair, not the complete model-backed product or a public release.

## Changes and source history

Original import: `ca819a902f5f8ac1bc18b10238505c3cd773cca6`. Its archive preservation and ten-test baseline remain under `../current-baseline/`.

The genuine delegated coding task `/root/tenderos_scoped_repairs` changed only `TenderOS/app/main.py` and `TenderOS/tests/test_workflows.py` in `/workspace/tenderos-fix`:

| Authored candidate | Integration branch commit | Change |
| --- | --- | --- |
| `3cbcb46acd1ceb17d937d9c2bbc913ed44817485` | `27fbb5d483d2f446c40c7298d5b6285fab5db894` | Source/evidence decision currency and spreadsheet formula escaping |
| `b8d99aa32abab9e46147eaac7ce93cdbb32307d4` | `aa2f87b03134dbfd05790692bf4769daed5c6016` | Strict attestation metadata types and literal XLSX error strings |

The orchestrator integrated those authored commits after both independent reviewers passed. Application and test bytes on the integration branch match the final tested candidate:

```text
app/main.py: 816183fdbd34acbeff18c3a08061adaeef43191b0e9615f1df4dd2c2f82609e0
tests/test_workflows.py: 087dfc61ffedcee1ea5c89a43416f27f70317152de93e28bd07125e899001d38
```

## Verified behavior

- Uploading an addendum with zero extracted candidates makes the old BID stale. Reattestation does not restore it; a new human decision is required.
- Source inventory, notice/source URL, requirement source association, requirement rationale and linked evidence metadata participate in currency checks. Expired or revoked evidence prevents a current BID.
- Each attestation uses its existing audit-event identity. A fresh attestation invalidates approval even when scope and second-resolution timestamps match. Metrics, unrelated evidence and unchanged reviews do not invalidate approval.
- Only the latest matching decision can be current. BID additionally requires `READY_FOR_HUMAN_DECISION`; unchanged HOLD/NO_BID may remain current in unresolved states.
- Legacy, incomplete, malformed or incorrectly typed snapshots remain historical. Float/bool attestation IDs cannot alias valid integer IDs. Read, rejection and export operations preserve decision rows and stored snapshot strings.
- CSV/XLSX escape formula-like prefixes in dynamic text. Every XLSX string serializes as text, including Excel error labels, numeric-looking strings and Bengali text. Numeric IDs/pages remain numeric. No spreadsheet formulas were evaluated.

Existing source attestations and decision snapshots from the original version do not automatically satisfy the new checks. Upgrading requires source reattestation and a fresh human decision; historical records are retained.

## Independent results

| Verification | Final result | Evidence |
| --- | --- | --- |
| Repository tests | 77 passed; no failures/errors/skips | [Repository output](qa/candidate-b8d99aa-original/repository.stdout.txt) |
| Frozen independent QA | 33 passed; no failures/errors/skips | [QA output](qa/candidate-b8d99aa-original/independent.stdout.txt) |
| Supplemental independent QA | 43 passed; no failures/errors/skips | [Supplemental output](qa/candidate-b8d99aa/supplemental.stdout.txt) |
| Independent security | 37 core + 44 edge checks passed | [Security verdict](security/FINAL-SECURITY-REVIEW.md) |

QA task `/root/tenderos_patch_qa` wrote the original independent harness before reading candidate source. Against the imported baseline, that same harness produced 21 passes and 12 defect failures; all 33 pass on the final candidate. Its supplemental harness produced 34 passes and nine defect failures against a read-only archive of the first candidate; all 43 pass on the final candidate. [Final QA report](qa/candidate-b8d99aa/QA_REPORT.md) records comparison, commands and trace IDs.

Security task `/root/tenderos_patch_security` separately inspected and tested the frozen candidates. The first candidate passed the initial checks but failed three additional cases: floating attestation ID and two Excel error strings. It was not accepted. [Original security findings](security/first-candidate-evidence/INITIAL-CANDIDATE-REVIEW.md) and failed outputs are preserved. The final 81-check review resolves those findings and adds further type/string cases.

The coding agent independently ran 77 tests successfully. Its expanded suite against the first candidate produced nine expected failures; against the original source the first expanded suite produced 34 expected failures. [First coder receipt](coder/coder-receipt.json) and [follow-up receipt](coder/security-followup/coder-receipt.json) retain exact commands, timestamps, source hashes and output hashes.

The installed Starlette/httpx combination emitted its existing TestClient deprecation warning. No test was skipped or failed on the final candidate.

## Runtime receipts, authority and limits

The user requested autonomous implementation and then objected to the agents stopping. The bounded private repairs proceeded under that session instruction. This does not assert approval of the complete draft PRD, a confidential-data processor or a production release.

Delegation used actual `collaboration.spawn_agent` / `collaboration.followup_task` calls. Canonical task identities and genuine tool traces are recorded in the receipts and review reports. The runtime exposes no separate opaque run ID; those fields remain null. The original stricter historical receipt gate is not represented as passed.

All verification used synthetic local data in external disposable runtime directories. No packaged customer database, private uploads, credentials or external model requests were used. Runtime databases/uploads are excluded from this evidence archive. Identity authentication, production tenant isolation and real model-powered specialist workflows remain outside these repairs.

## Evidence storage and replay

[EVIDENCE_COPY.json](EVIDENCE_COPY.json) maps original execution files to byte-identical archived copies. [Output hashes](output-hashes.json) cover the stored evidence and reports. Agent-authored manifests retain their original filenames and execution paths.

Test harness source is stored with `.py.txt` filenames to prevent repository pytest from collecting the verification archive or creating runtime data there. For replay, copy the harnesses and runners into a separate disposable directory and restore their original filenames. Recorded commands and environment overrides in the receipts identify the tested source commit, external data locations and installed interpreter. The archived scripts are execution evidence; run the application suite from `TenderOS/tests/` for ordinary development.
