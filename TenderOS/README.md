# TenderOS — Bid Decision Intelligence

**Repository integration status:** original local MVP source imported unchanged on 2026-10-09. Baseline and independent audit evidence are under `verification/`. The agentic product implementation remains subject to the PRD and engineering gates.

## Existing repository
The existing `ProposalGuard/` directory is an independent TenderProof OS / ProposalGuard archive. Preserve it. TenderOS must be imported into its own `TenderOS/` directory; do not overwrite `ProposalGuard/` or the default branch.

## Intended functionality
TenderOS assesses tender eligibility and organization evidence, identifies mandatory blockers and unresolved claims, and prepares a source-traceable compliance matrix for an authenticated human BID / NO-BID / HOLD decision.

## Imported source and project knowledge
The supplied `TenderOS_Codex_Work_Transfer_v1_2.zip` provides the FastAPI application, static UI, ten baseline tests, dependency manifest, PRD, APES documentation and agent contracts. Its `repo/` files have been mapped into this directory, while its knowledge, agent-operations and verification files retain their corresponding subdirectories.

The application and tests retain the ZIP's original bytes. The existing repository `AGENTS.md` remains active. The transfer's original repository instructions and README are preserved in `verification/TRANSFER_REPO_AGENTS.md` and `verification/MVP_README_ORIGINAL.md`.

The ZIP contains a SQLite database despite its documentation saying the database was omitted. The entire archived `repo/data/` tree was excluded. No packaged database or customer uploads were imported.

See [import mapping and hashes](verification/IMPORT_REPORT.json), [current source audit](verification/CURRENT_SOURCE_AUDIT.md), and the [draft PRD](project_knowledge/02_PRD_v1_1.md). The handoff ZIP's nine documents are byte-identical to the corresponding transfer knowledge files, so they were imported once.

Independent verification on 2026-10-09: **10 tests passed, none skipped or failed**; `/api/health`, `/`, and `/api/docs` returned 200 through the local test client. [Current results](verification/current-baseline/baseline-result.json) and [test output](verification/current-baseline/baseline.stdout.txt) are preserved.

Import instructions: [IMPORT_EXISTING_SOURCES.md](IMPORT_EXISTING_SOURCES.md).

## Run the local prototype

From the repository root, using Python 3.11 or newer:

```bash
cd TenderOS
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
TENDEROS_DATA_DIR=/tmp/tenderos-local .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`; API documentation is at `/api/docs`. Set `TENDEROS_DATA_DIR` before application import to keep runtime data separate from the source tree.

For the complete baseline, install the optional PDF-test dependency and run:

```bash
.venv/bin/python -m pip install reportlab
TENDEROS_DATA_DIR=/tmp/tenderos-baseline PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

Without `reportlab`, the existing PDF provenance test skips. Resolved versions and current test results are recorded in `verification/current-baseline/`; dependency ranges remain unchanged from the original source.

## Engineering evidence and gates
No autonomous AI sub-agent, no build. Read [AGENTS.md](AGENTS.md). Actual delegated agents performed source/archive audits and unchanged-source import, with separate independent QA. Their canonical task identifiers and tool traces are recorded. The launcher does not expose a separate opaque run ID; this receipt limitation is explicit rather than represented as a passed strict gate. The source migration introduces no new application logic.

The draft PRD and supplied `START_HERE.md` require founder approval of the bounded implementation scope before T-003. The first proposed change is DEF-001: source/evidence changes must invalidate a current BID while preserving decision history. No implementation repair, merge or deployment is included in the import.

## Current limitations
- Local FastAPI/SQLite prototype without authenticated multi-user access.
- PDF candidates come from local keyword heuristics; model-powered specialist tasks are proposed in the PRD.
- Source/evidence references and reviewer identities need stronger validation before external use.
- DEF-001 is unresolved: a zero-candidate addendum changes source completeness without invalidating the displayed BID.
- XLSX header exports interpret formulas in tender title and decision reviewer/rationale; independently reproduced with a benign synthetic formula.
- Baseline test success does not prove a working model-backed workflow or production readiness.
- External tender submission and production deployment require their separate gates.

Do not publish confidential tender files, scanned books, secrets, customer evidence or local databases to GitHub.
