# TenderOS Source Import — safe handoff

**Status: unchanged-source import executed on 2026-10-09.** The supplied artifact was `TenderOS_Codex_Work_Transfer_v1_2.zip`; its layout differs from the originally named Git import ZIP. The executed mapping, original source hashes, governance preservation and exclusions are recorded in [verification/IMPORT_REPORT.json](verification/IMPORT_REPORT.json). The archived `repo/data/` tree was excluded, including the SQLite database that the transfer documentation incorrectly described as omitted. The procedure below preserves the original handoff requirements; execution evidence and current test results are in `verification/`.

## Target
- GitHub: `mdsyfulhoque-afk/tender` (private)
- Existing base: `main`, with `ProposalGuard/` already present
- Integration branch: `tenderos/import-v1.2`
- Source import location: `TenderOS/` (never repository root)

## Steps
1. Open a persistent Codex/Work coding environment connected to the GitHub repository.
2. Attach or mount `TenderOS_Git_Import_v1_2.zip` from the TENDER TO FIT project conversation.
3. Run T-000 through an actual delegation interface and preserve two independently executed read-only agent receipts; if unavailable STOP. (Import of the unchanged archive is a repository migration, not an application-code build.)
4. Audit the archive for path traversal and unintended sensitive files.
5. On `tenderos/import-v1.2`, unpack into `TenderOS/`. Confirm the expected 31 tracked files, including `app/main.py`, `app/static/ui.js`, `tests/test_workflows.py`, `requirements.txt`, the Fresh Constitution and PRD.
6. Do not import `data/tenderos.sqlite3`, user uploads, secret files, caches or e-GP scanned publications.
7. Run `python -m pytest -q` from the `TenderOS/` directory after installing `requirements.txt` in a disposable virtual environment.
8. Confirm app source checksums against the original archive before committing. Record discrepancies.
9. Commit on the integration branch, submit a PR and request human review. Never force-push or merge without approval.
10. Independently verify that real agent-run receipts exist before starting defect fixes.

## Codex launch brief
Read `TenderOS/AGENTS.md` and after archive import read `TenderOS/agent_ops/CODEX_LAUNCH_IN_WORK.md`, the APES Master, Constitution, PRD and task graph. For T-000, launch two distinct READ-ONLY agents and retain their actual IDs, command histories and SHA-256 output artifacts. No launched sub-agent => NO BUILD.

## Current known defect
DEF-001: source inventory can change after an approved BID without current_decision becoming stale. The product must retain immutable historical decisions but reject presenting an outdated BID as current.

## Veracity policy
Do not label this integration manifest a complete source migration, a production release, or proof that any Codex worker ran.
