# ART-300 — Genuine Autonomous Sub-agent Delegation Contracts
**Status: REVIEW_READY. Nothing below claims that an agent has executed.**

## Founder's hard requirement
An implementation task is forbidden without an actual delegated AI software agent that receives a bounded objective, independently executes tool calls, returns tangible artifacts and observable run evidence, and is challenged by a separate QA role. Persona labels and synthesized dialogue fail this gate.

## Runtime proof (`AGENT_RUNTIME_OK`) — absolute prerequisite
1. Run a harmless isolated read-only task with separate delegated execution (e.g., inspect test names and summarize dependencies).
2. Capture runner name and method, agent ID, actual run ID, task start/end, scope, tools called, actual tool events, output artifact hashes.
3. Have a second separately invoked review agent independently examine first agent's artifact and publish findings with different run ID.
4. Orchestrator checks both receipts and that neither agent fabricated tool activity.
5. On failure set `AGENT_RUNTIME_BLOCKED`; STOP before source modification.

This contract does not demand one particular vendor/framework; it demands independently verifiable operation.

## Delegation safety
- Agents operate in separate branches/worktrees or isolated staging dirs; the orchestrator controls merging.
- Agents receive least-privilege filesystem/tool permissions; no secrets, no unapproved network; no live bidder data.
- No self-approval: coder cannot review or accept its own changes.
- Every agent has max task duration, max tokens/tool calls, allowed files, forbidden actions and stop conditions; operations are recorded.
- Enforce owner approvals for source-code release, model egress, customer data, bid decisions, payments and public deployment.

## Development sub-agents

### AG-R01 — Repo & Domain Evidence Scout
**Objective:** Inspect exact baseline repo and source PDFs; enumerate real capabilities, defects and legal-source unknowns.
**Permitted inputs:** local source, tests, README, Blueprint, APES master, TenderToFit Constitution, attached e-GP scans.
**Permitted tools:** read-only filesystem, code search, tests in temporary test directory, PDF visual inspection.
**Forbidden:** application source changes, model calls on confidential data, e-GP login/scraping.
**Outputs:** `repo_audit.json`, `domain_evidence.md`, risk items with paths/sections, tool-event receipt.
**Acceptance:** Every claimed feature maps to code path/test; distinguishing book from binding official procurement rules.

### AG-A02 — Architecture & API Contract Engineer
**Objective:** Prepare the simplest bounded model-backed vertical slice reusing existing core.
**Dependencies:** AG-R01 audited, privacy and runtime gate.
**Outputs:** ADRs, input/output schemas, trust-boundary diagram, source version plan, draft migrations, cost/latency budget.
**Forbidden:** unnecessary microservices, premature paid API mandates, replacing deterministic compliance with LLM.
**Acceptance:** source/provenance/approval invariants testable; agent tasks separated from business approval.

### AG-I03 — Implementation Coding Agent
**Objective:** First fix DEF-001 in an isolated worktree, only after owner and runtime gates; subsequent independently approved tasks build provider gateway and agents.
**Inputs:** frozen PRD, approved ADR, exact task packet, local code, existing tests.
**Allowed files task 1:** `app/main.py`, `tests/test_workflows.py`; task log in separate working dir.
**Forbidden:** deletes, database exfiltration, network access, external model call, release/merge.
**Deliver:** git diff, changed-file hashes, tests run, bug reproduction before/after, known limitations, unique agent run ID.
**Acceptance DEF-001:** zero-candidate addendum invalidates active BID display; adding source or changing verified evidence invalidates decision as appropriate; unrelated changes don't corrupt history; all existing tests pass.

### AG-Q04 — Independent QA and Red-team Agent
**Objective:** Reproduce or falsify coder claims; test negative and adversarial cases, inspect privacy regressions.
**Dependencies:** separate invocation after implementation output.
**Forbidden:** approving its own patch; unilateral merge/deploy.
**Outputs:** independent test logs, regression report, findings severity, accept/reject decision with run ID.
**Acceptance:** detects at least the originally reproduced failure, validates fixed behaviour using independent tests, test-suite status and artifact hashes.

### AG-S05 — Security/Privacy Reviewer
**Objective:** Evaluate data egress, authentication/tenant boundaries, malicious PDF handling, prompt injection, secret hygiene.
**Inputs:** architecture + candidate diff.
**Outputs:** threat model updates, security issue register, go/no-go recommendation.
**Acceptance:** sensitive PDFs never sent to a model without policy approval; test tenant crossing and forged BID approval.

### AG-C06 — Commercial Benchmark Analyst
**Objective:** Create reproducible supervised test protocol and pricing hypotheses from approved inputs.
**Outputs:** sample design, time-cost instrumentation, comparator worksheet specification, pilot exit gates.
**Forbidden:** inventing paid customer data, legal rules, model prices or success rates.
**Acceptance:** distinguishes free demo, quoted price, actually paid price, first order, repeat order.

## Product-time agents, distinct from development agents
- `PA-REQ` — LLM parses and classifies possible tender clauses with source citations; unverified suggestions only.
- `PA-EVD` — LLM searches company evidence via tenant-scoped tools and proposes structured relevance links; cannot verify its own output.
- `PA-VER` — independent model/person verifies source-match candidate; all important findings still require human approval.
- `PA-OPS` — deterministic orchestrator for task state, retry, budget and review queues; does not act as business decision maker.

## Evidence receipt example (SCHEMA EXAMPLE ONLY, not an actual execution)
```json
{
  "task_id": "T-001",
  "agent_id": "AG-I03",
  "runner": "TO_BE_CONFIRMED",
  "run_id": "REQUIRED_REAL_ID",
  "status": "NOT_RUN",
  "workspace": "ISOLATED_WORKTREE_REQUIRED",
  "allowed_files": ["app/main.py", "tests/test_workflows.py"],
  "tool_events_uri": null,
  "diff_hash": null,
  "test_log_hash": null,
  "reviewer_run_id": null,
  "owner_gate": "PENDING"
}
```

## Concrete rollout sequence
`T-000 runtime proof -> T-001 read-only audit -> T-002 independent audit review -> owner approves PRD -> T-003 DEF-001 isolated fix -> T-004 independent regression/security review -> controlled merge -> T-005 model gateway consent boundary -> T-006 actual requirement agent -> T-007 actual evidence agent -> T-008 verification + benchmark -> owner release gate`.
