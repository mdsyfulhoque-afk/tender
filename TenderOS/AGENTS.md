# TenderOS — Autonomous Codex / Work engineering policy

## Governing restriction
**NO AUTONOMOUS AI SUB-AGENT, NO BUILD.**

Only a genuinely independent, separately launched AI coding sub-agent with verifiable runtime identity, run ID and tool execution trace may modify application code. A simulated persona, a sequential ordinary model message, a shell script or a GitHub Actions job is NOT an autonomous AI sub-agent.

If no delegated agent launcher exists, report `AGENT_RUNTIME_BLOCKED` and do not alter application source. Do not fabricate tool names, run logs, or agent identities.

## Domain laws
- Bid Decision Intelligence, not general proposal writing.
- Tender text / official documents outrank derived summaries.
- Keep source page, section, excerpt and version provenance.
- A mandatory `NOT_HELD` is a blocker.
- Mandatory `UNKNOWN`, `PARTIAL`, unverified requirement or incomplete tender source inventory keep readiness unresolved.
- A BID cannot be considered current unless requirements, evidence and source inventory are current, and there is authorized human approval.
- No inferred eligibility from silence, no fabricated win-probability scoring.
- Do not disclose customer evidence to cloud models without explicit approval.
- Preserve private tenant boundaries, historical decisions and review logs.
- No automatic bid submission, financial commitment, live e-GP login or uncontrolled crawling.

## Executable agent sequence
1. T-000: verify a **real** delegated-agent API/runtime; record tool name, agent ID, run ID, timestamps and trace locations.
2. T-001: independent read-only architecture/domain agent audits actual imported source.
3. T-002: separately launched read-only verifier reproduces the findings.
4. Founder reviews the PRD and approves the bounded implementation scope.
5. T-003: isolated autonomous coding agent fixes the approved defect (start with DEF-001).
6. T-004: separate QA/security sub-agent tests the change; independently review before PR merge.

## Minimum trace record
```yaml
task_id:
agent_runtime:
delegation_tool:
agent_id:
run_id:
start_end_utc:
branch_or_worktree:
allowed_tools_and_permissions:
source_hashes:
tool_logs_location:
output_sha256:
test_results:
independent_reviewer_run_id:
data_egress:
open_risks:
```

Missing evidence means STOP, not PASS. Never merge, deploy or overwrite existing ProposalGuard without explicit authorization.
