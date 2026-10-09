# ART-020/ART-200 — Existing TenderOS Code Audit
**Status:** REVIEW_READY for human evaluation; no deployment approval.

## Scope and provenance
Inspected `/mnt/data/tenderos_mvp/README.md`, `app/main.py`, `requirements.txt`, `tests/test_workflows.py`, `docs/COMPANY_BLUEPRINT.md`, archive manifest. Ran existing pytest suite unchanged and a separate disposable synthetic regression scenario. Existing business context taken from the TenderToFit Constitution and APES master documentation in the project Library.

## Confirmed functionality
| Component | Actual implementation | Assessment |
|---|---|---|
| UI | Static HTML/CSS/JS served by FastAPI | Local single-user pilot; no production auth |
| Backend | Python FastAPI, single `app/main.py` (~31 KB) | Core routes exist; modularization recommended after approval |
| Storage | SQLite with local private PDF paths | Not multi-tenant-secure or encrypted; do not expose externally |
| PDF processing | `pypdf`, regex-based English candidate extraction | Text PDF only; may omit tables, Bengali conditions, scanned docs |
| Requirements | Page and quotation fields, review flag, mandatory tri-state | Need immutable source span and revision model |
| Company evidence | Manual reference/label, verified flag, note, expiry | No attachment validation or cryptographic issuer check |
| Compliance | Deterministic mandatory blockers and unresolved statuses | Retain as non-LLM core |
| Approval | Named human field and reason | Self-asserted text, not authenticated approval |
| Output | CSV, XLSX, DOCX | Editable; limited demonstrated report integrity |
| Audit | Local SQL `audit_events` rows | Not tamper-proof and actor not authenticated |
| Commercial | Quote/payment/effort metrics | Useful pilot signals; no invoice verification |
| Agents | None in code | Existing MVP is not AI-native |

## Executed tests
- Existing suite: `PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q` -> **10 passed in 0.69 s**.
- Additional independent run: FastAPI TestClient, temp SQLite directory, synthetic approved BID, then upload text PDF addendum with no keyword candidate.
- Before upload: `current_decision=BID`, `compliance=READY_FOR_HUMAN_DECISION`, `source_scope_verified=True`.
- After upload: `candidates=0`, `current_decision=BID`, `compliance=UNRESOLVED`, `source_scope_verified=False`.
- **Confirmed release-blocking bug (DEF-001): stale current BID approval when source inventory changes without modifying extracted requirement list.** Decision-current logic compares requirement fingerprint only. Source documents are excluded from that decision fingerprint, although source-completeness attestation changes. Requirement: invalidate active approval whenever any source/addendum change affects assessment scope. Regression test must cover empty-candidate addenda and changed evidence revisions.

## Security and correctness findings
- **SEC-001 Critical:** API has no authentication or tenant authorization, despite routes to list organizations/tenders and fetch assessment data. Suitable only for isolated local testing.
- **SEC-002 Critical:** Approval reviewer's name is supplied by request body and cannot establish human identity/role.
- **SEC-003 High:** Confidential evidence is a string reference, not verified proof; the interface must not imply issuer verification.
- **SEC-004 High:** Parsing uploaded PDFs is not sandboxed and does not include antivirus/malware scanning; size/page caps are useful but incomplete.
- **DOC-001 High:** Candidate extractor is English keyword regex and `pypdf` text, excludes Bengali/scanned images and can split legal clauses incorrectly. Source-completeness human review compensates only if performed correctly.
- **SRC-001 High:** Source page and quotation are not enough for robust quote grounding; candidate matching to immutable source spans/hash needed.
- **OPS-001 Medium:** No background queue, job state, idempotency keys, retries or token budgets.
- **DB-001 High:** SQLite lacks authenticated row isolation; evidence matching rejects wrong organization at application layer only.
- **AUD-001 High:** Audit rows are writable/erasable by local filesystem owner; no WORM / signed chain.
- **DEV-001 Medium:** No `.git` history in current local folder; initialize only after approved source preservation plan.
- **AI-001 Blocking:** No actual LLM calls, no sub-agent runtimes, no saved tool traces or autonomous coding receipts.

## Prioritized remediation gates
1. DEF-001 stale BID approval + regression test. Do not permit customer use until fixed and independently verified.
2. Real delegated-agent runtime must be available **before any implementation task** per founder instruction.
3. Freeze core domain rule tests and add exhaustive source/addendum/evidence invalidation scenarios.
4. Implement real model-backed retrieval and extraction only behind an explicit privacy and egress configuration.
5. Auth + permissions + tenant isolation required before any external/multi-user release.

## Assertions NOT supported
- NOT a deployed SaaS; NOT enterprise multi-tenant-secure; NOT autonomous; NOT production validated; NOT compliant with every BPPA procedure; NOT proof of a profitable business.
