# Current TenderOS source audit

Date: 2026-10-09. Source archive SHA-256: `7786d9785ebf6c8db21b547f174277f872f20a15a58219c36dc70642d9a33867`.

This audit distinguishes the imported implementation from the draft PRD. The independent source auditor was `/root/tenderos_repository_audit`; the separate archive/QA verifier was `/root/tenderos_independent_verification`. Actual task identifiers and transcript evidence are recorded; separate opaque runtime run IDs are not exposed. The existing strict receipt requirement has not been declared passed.

## Implemented local workflow

The source provides a FastAPI/SQLite application and a static JS interface. It registers organizations and tender assessments, stores uploaded PDFs privately with SHA-256 hashes, extracts English keyword candidates with `pypdf`, reviews and classifies requirements, links organization-owned evidence references, evaluates mandatory compliance deterministically, records source-completeness attestations, appends human decision records, exports CSV/XLSX/DOCX matrices, and records pilot metrics.

The ten original tests cover mandatory blockers, review gates, evidence expiry, cross-organization evidence mapping, exports/metrics, PDF provenance, health/demo, missing source provenance, requirement-change decision invalidation and one XLSX formula-injection case. Independent execution passed all ten tests with zero skips/failures; the PDF test ran with `reportlab` installed. Health, root UI and API docs returned 200 through `TestClient`. Health reports `LOCAL_PILOT` and `external_model_calls: false`. Current results and resolved dependencies are saved separately in `current-baseline/`; historical transfer logs are not treated as new results.

## Implementation gaps

- No working model connection or product-time AI analyst tasks. `/api/health` declares external model calls disabled.
- No authenticated reviewer identity or secure multi-user/tenant access boundary.
- PDF extraction is heuristic, without OCR or Bengali-aware extraction.
- Source page/quote annotations are not checked against immutable source spans.
- Evidence records contain references and self-declared verification rather than versioned evidence attachments.
- Requirement updates occur in place; the prototype does not provide a complete immutable revision model.
- Durable model jobs, retries, cost budgets and agent observability are proposed, not implemented.
- Payment metrics are recorded entries, not verified payment processing.

The APES master was read by the source audit agent through its DOCX XML (2,106 paragraphs). Relevant requirements are staged lifecycle gates, reviewed evidence/artifacts, regression and acceptance checks, local privacy, source provenance and a core that does not require paid APIs or hosting. The later Fresh Constitution governs the current mandatory-status decision laws.

## DEF-001: current BID ignores source-set changes

`app/main.py:227` constructs a source-scope fingerprint using the source inventory and requirement definitions. `app/main.py:234` constructs a separate decision fingerprint using requirement/effective-status fields. Decision snapshots save both values at `app/main.py:399`, but `app/main.py:250` determines currency using only the requirement fingerprint.

Every uploaded PDF is registered as a source. A PDF containing no candidate keywords changes the source inventory without changing requirements. Source attestation consequently becomes stale and compliance is unresolved, while the old BID can still be exposed as current. The UI trusts the API's currency flag.

Independent executable reproduction confirmed the causal finding with synthetic data. Before upload, compliance was `READY_FOR_HUMAN_DECISION`, source scope was verified, and current decision was BID. After a PDF upload returning `candidates: 0`, compliance was `UNRESOLVED`, source scope was unverified, but current decision remained BID and `is_current` remained true. A new BID attempt correctly returned 409. Stored decision rows and their canonical hash remained unchanged, confirming historical preservation. Exact observed states are stored in `current-baseline/DEF-001-reproduction.json`.

## Proposed bounded T-003 repair

Allowed application changes: `app/main.py` and `tests/test_workflows.py` only.

1. Require current source-scope and requirement/evidence state to match the approved decision snapshot.
2. Treat legacy snapshots missing the required currency metadata as historical.
3. Preserve historical decisions and their original snapshots.
4. Add regressions for zero-candidate addenda, requirement/source changes, relevant linked-evidence changes/expiry and unrelated changes that must not corrupt history.
5. Run the original baseline and new meaningful regressions, then obtain independent QA/security verification in a separate agent execution.

The supplied PRD and START_HERE require founder approval before this implementation task. Source import is completed; DEF-001 has not been repaired. Model gateway and product-time agents remain later scoped tasks, subject to the processing/privacy decisions in the PRD.

## Confirmed XLSX export defect

Independent QA confirmed that benign `=1+1` values in tender title and decision reviewer/rationale are stored as formula cells (`data_type: f`) at `Compliance Matrix!B2`, `Decision History!B2` and `Decision History!C2`. No formulas were evaluated. The existing baseline formula-injection test covers only a requirement cell and misses these fields. Evidence is in `current-baseline/XLSX-formula-observation.json`.

A separate bounded fix should serialize every untrusted XLSX field as literal text and add regressions for these three cells while preserving existing export contents and baseline behavior. This would use the same two application/test files as DEF-001 but requires an explicit scope decision.

## Archive and provenance findings

Independent archive review checked paths, regular-file modes, collisions, expansion limits, CRCs of safe members, manifest sizes/hashes, source-preservation records and the embedded APES DOCX structure. All nine handoff documents equal their corresponding transfer knowledge files.

The packaged database contradicts the supplied omission claim and was excluded from import. Internal preservation records are consistent with the archive; they do not prove comparison against an independently accessible older baseline. Existing branch governance and prior receipts were retained; archived repository AGENTS/README remain available as provenance.

The new Drive URL could not be read because the Google Drive connector returned `USER_NOT_LOGGED_IN`. The uploaded source bundle and handoff were used for this audit.
