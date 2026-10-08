# TenderOS — Bid Decision Intelligence

**Repository integration status:** governance/handoff only. The local MVP source has not yet been uploaded to this remote branch. Do not call this a runnable release.

## Existing repository
The existing `ProposalGuard/` directory is an independent TenderProof OS / ProposalGuard archive. Preserve it. TenderOS must be imported into its own `TenderOS/` directory; do not overwrite `ProposalGuard/` or the default branch.

## Intended functionality
TenderOS assesses tender eligibility and organization evidence, identifies mandatory blockers and unresolved claims, and prepares a source-traceable compliance matrix for an authenticated human BID / NO-BID / HOLD decision.

## Required import artifact
`TenderOS_Git_Import_v1_2.zip` prepared in the TENDER TO FIT ChatGPT project. Its contents include FastAPI app source, JS UI, baseline tests, project knowledge, PRD, APES documentation and governance contracts. The archive remains an attached ChatGPT artifact; it has **not** been incorporated into this GitHub tree.

Import instructions: [IMPORT_EXISTING_SOURCES.md](IMPORT_EXISTING_SOURCES.md).

## Hard engineering gate
No autonomous AI sub-agent, no build. Read [AGENTS.md](AGENTS.md). Until distinct independently launched agents have produced real run IDs and traces, application code modifications are blocked.

## Current limitations
- Local FastAPI/SQLite prototype; no authenticated multi-user SaaS.
- Model-powered task execution has not been established.
- Historical local tests passed 10/10, but those tests do not prove readiness or safety.
- DEF-001: stale approved BID may remain displayed after an addendum; must be addressed after independent audit, scope approval, autonomous coding execution and separate QA.
- No external tender submission or production deployment authorized.

Do not publish confidential tender files, scanned books, secrets, customer evidence or local databases to GitHub.
