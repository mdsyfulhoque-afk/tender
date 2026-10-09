# TenderOS — Codex repository instructions (v1.2)

## Highest priority: founder execution rule
NO AUTONOMOUS AI SUB-AGENT, NO BUILD. Only genuine, separately launched autonomous coding agents with observable run IDs and tool traces may implement code changes. If the environment cannot spawn an independent delegated agent, emit `AGENT_RUNTIME_BLOCKED` and do not modify application source.

## Project identity and authority
- TenderOS is Bid Decision Intelligence, not generic proposal writing.
- `../project_knowledge/TENDERTOTFIT_FRESH_CONSTITUTION.md` is the normative product baseline.
- Consult `../project_knowledge/APES_TenderToFit_Final_Master_Documentation_V1_0.docx` and `02_PRD_v1_1.md` for lifecycle, artifacts, gates and acceptance criteria.
- The existing FastAPI app is a LOCAL MVP, no remote AI calls or auth. Do not call it production ready.
- No source edits before separately executed read-only audit AG-R01 and independent reviewer AG-Q04, each with genuine distinct run IDs, plus founder approval for scoped code implementation.

## Hard rules
- NEVER self-approve a sub-agent's findings. Reviewer must be separately launched.
- Preserve immutable source evidence, exact page/section provenance and append-only decision history.
- `NOT_HELD` mandatory blocks; mandatory `UNKNOWN`, `PARTIAL`, unverified and incomplete documents keep unresolved; no inferred compliance.
- Do not present a win probability. Human approves final BID/NO-BID/HOLD.
- Never send confidential tenders or company evidence to external model without specific security/privacy approval.
- No submission automation, live e-GP login/scraping, CRM, proposal drafting, financing or autonomous external communication in current scope.
- Cost gate: no mandatory paid runtime APIs or hosting for the core workflow.
- For every actual agent run, provide true runtime, run ID, permissions, tool trace, artifact hashes, tests, reviewer ID, and blockers. Unknown means unknown, not success.

## Initial issue (DEF-001)
An approved BID remains exposed as current after uploading a zero-keyword addendum: `compliance=UNRESOLVED`, but `current_decision=BID`. First approved coding task must invalidate current display while keeping immutable decision history; regression tests must cover addenda, changed source inventory and evidence.

## Initial execution order
See `../agent_ops/CODEX_LAUNCH_IN_WORK.md`, task graph and `../project_knowledge/03_AUTONOMOUS_SUBAGENT_CONTRACTS.md`.
T-000 verify real delegated runtime (read-only) -> T-001 independent repo/domain audit -> T-002 separate QA review -> founder scope approval -> T-003 isolated DEF-001 fix -> T-004 separate QA and security review. No automatic merge/deploy.
