# TenderOS — Bid Decision Intelligence

**Repository integration status:** original local MVP imported on 2026-10-09, followed by scoped repairs to decision currency and spreadsheet exports. Independent verification and actual agent receipts are under `verification/`. This remains a local pilot; the model-backed product workflow is described in the draft PRD.

**Vercel preparation:** branch `tenderos/deploy-vercel` adds a protected single-owner hosted mode with managed PostgreSQL, private Vercel Blob storage, authenticated reviewer identity and CSRF protection. See [deployment instructions](DEPLOY_VERCEL.md) and [deployment preparation evidence](verification/vercel-preparation/REPORT.md). The hosted changes passed independent static review; unit tests and live provider validation have not run for this candidate. Deployment is pending an authenticated Vercel workspace and API network access.

## Deployment access followup

The Vercel Git integration reacted to deployment head `fbe96b4f51c7400d9ada1bdf2fe763fef54c4f07`, but its status failed: "Git author IP3consulting must have access to the project on Vercel to create deployments." The [Vercel bot comment on PR #2](https://github.com/mdsyfulhoque-afk/tender/pull/2#issuecomment-6087417578) confirms a team access requirement. Its successful preview-comment check only confirms that the bot posted a comment.

The connected GitHub account is `mdsyfulhoque-afk`; this documentation update is submitted through that authenticated connection, with no author override or history rewrite. Vercel will evaluate the actual new commit identity. The user confirmed their supplied access is the Vercel plugin connection. Current cloud observations still show no CLI login, token secret or supported Vercel API network access. Project configuration, managed resources and live deployment remain unverified.

## Existing repository
The existing `ProposalGuard/` directory is an independent TenderProof OS / ProposalGuard archive. Preserve it. TenderOS must be imported into its own `TenderOS/` directory; do not overwrite `ProposalGuard/` or the default branch.

## Intended functionality
TenderOS assesses tender eligibility and organization evidence, identifies mandatory blockers and unresolved claims, and prepares a source-traceable compliance matrix for an authenticated human BID / NO-BID / HOLD decision.

## Imported source and project knowledge
The supplied `TenderOS_Codex_Work_Transfer_v1_2.zip` provides the FastAPI application, static UI, ten baseline tests, dependency manifest, PRD, APES documentation and agent contracts. Its `repo/` files have been mapped into this directory, while its knowledge, agent-operations and verification files retain their corresponding subdirectories.

Import commit `ca819a902f5f8ac1bc18b10238505c3cd773cca6` preserves the ZIP's original application and test bytes. Subsequent repairs are recorded separately in Git and [the repair report](verification/scoped-repairs/REPORT.md). The existing repository `AGENTS.md` remains active. The transfer's original repository instructions and README are preserved in `verification/TRANSFER_REPO_AGENTS.md` and `verification/MVP_README_ORIGINAL.md`.

The ZIP contains a SQLite database despite its documentation saying the database was omitted. The entire archived `repo/data/` tree was excluded. No packaged database or customer uploads were imported.

See [import mapping and hashes](verification/IMPORT_REPORT.json), [imported-source audit](verification/CURRENT_SOURCE_AUDIT.md), and the [draft PRD](project_knowledge/02_PRD_v1_1.md). The audit documents the original baseline and its defects; repair results supersede those defect statuses. The handoff ZIP's nine documents are byte-identical to the corresponding transfer knowledge files, so they were imported once.

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

For the complete test suite, install the optional PDF-test dependency and run:

```bash
.venv/bin/python -m pip install reportlab
TENDEROS_DATA_DIR=/tmp/tenderos-baseline PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

Without `reportlab`, PDF tests skip. The original baseline and dependency versions are recorded in `verification/current-baseline/`; repair verification is in `verification/scoped-repairs/`. Dependency ranges remain unchanged from the original source.

## Engineering evidence and gates
No autonomous AI sub-agent, no build. Read [AGENTS.md](AGENTS.md). Actual delegated agents performed source/archive audits, source import and scoped coding in an isolated worktree. Separate QA and security agents reviewed the completed commits using synthetic local data. Canonical task identifiers, commands, hashes and actual tool traces are recorded. The launcher does not expose a separate opaque run ID; this receipt limitation is explicit rather than represented as a passed strict gate.

The user's session instruction to continue autonomous development authorized the bounded private repairs. This does not assert approval of the full draft PRD or an external model processor. Historical transfer instructions and their original status claims are preserved. The changes remain on the draft integration branch.

## Decision and export repairs

- Source inventory, source associations, requirement rationale and linked evidence values participate in decision currency checks. A current BID also requires current readiness.
- Each source attestation has an existing audit-event identity. Reattestation requires a fresh decision, including when the source content is unchanged and timestamps match.
- Legacy or malformed snapshots remain historical and cannot become current. Existing assessments need source reattestation and a new human decision after upgrading; stored decision rows are retained.
- Spreadsheet exports escape formula-like prefixes in dynamic text. XLSX strings, including Excel error labels, are serialized as literal text; numeric IDs and pages remain numeric.

## Current limitations
- Local FastAPI/SQLite mode and prepared hosted PostgreSQL/private Blob mode. Hosted access is for one configured owner; there is no multi-user customer or role system.
- PDF candidates come from local keyword heuristics; model-powered specialist tasks are proposed in the PRD.
- Source/evidence references and reviewer identities need stronger validation before external use.
- Baseline test success does not prove a working model-backed workflow or production readiness.
- External tender submission and production deployment require their separate gates.

Do not publish confidential tender files, scanned books, secrets, customer evidence or local databases to GitHub.
