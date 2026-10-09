# T-004 independent QA result

Candidate `3cbcb46acd1ceb17d937d9c2bbc913ed44817485` passed all 52 repository
tests and all 33 independently authored cases. There were zero failures,
errors or skips. The exact same independent harness failed 12 of its 33
cases on imported baseline `ca819a902f5f8ac1bc18b10238505c3cd773cca6`.
All 12 baseline failures now pass; the 21 baseline passes remain passing.

The independent harness was written and exercised before candidate source
was read. It confirms zero-candidate addenda invalidate prior BID approval;
source re-attestation does not resurrect it; same-scope re-attestation and
revocation/re-attestation invalidate approval even when timestamps are
identical; source association/content and linked evidence changes invalidate
approval; revoked/expired evidence prevents BID; incomplete legacy snapshots
remain historical; and new approval can become current on ready state.

Historical decision rows and snapshot strings remain unchanged during the
checked workflows. Unchanged reviews, unrelated evidence, metrics and export
reads preserve current approval. Explicit HOLD and NO_BID remain current in
unchanged unresolved states. XLSX title, reviewer, rationale, requirement,
quote, evidence label and notes are stored as strings for four formula-like
prefixes with empty/spaces/tab/CRLF prefixes. Numeric fields remain numeric.
No spreadsheet calculation was performed.

Source and test hashes were identical before and after execution and match
the coding-agent candidate:

```text
main.py: 5377bf1e87eff9e0641ceb5103b96aa1bad978690ab6551375bdb7189777b5b0
test_workflows.py: d636814627614a150696c33394ccec88b19a94f9eb5af834612996b650614bda
frozen independent harness: 840f3438973fdd4d18579c44ca3fcab98276fe0f7ec49ada131e8493289b752d
```

The worktree remained clean and HEAD was checked again after the tests.
A read-only diff review found currentness tied to requirement/evidence state,
source inventory and actual attestation event identity, with readiness needed
for BID, immutable historical rows, and shared spreadsheet literal escaping.
No actionable defect was found within the bounded repair scope.

Exact parent command:

```text
/workspace/.venvs/tenderos-baseline/bin/python /workspace/tenderos-independent-qa/run_qa.py --source /workspace/tenderos-fix/TenderOS --label candidate-3cbcb46 --expected-commit 3cbcb46acd1ceb17d937d9c2bbc913ed44817485 --with-original-suite
```

Exact suite argv, UTC timings, resolved dependency versions, source hashes,
environment overrides and scope declarations are in `result.json`. Captured
stdout/stderr, JUnit XML and synthetic in-process request traces are present;
`artifact-hashes.json` hashes those execution artifacts. Actual tool response
chunks are `d29583` (execution launch), `e54647` (successful completion),
`e48b33` (read-only diff and unchanged HEAD/worktree), and `102b9a` (captured
test results and artifact hashes).

Runtime identity is `/root/tenderos_patch_qa`, dispatched with
`collaboration.spawn_agent` and resumed with `collaboration.followup_task`.
No separate opaque run ID is exposed; none was invented. This receipt reports
bounded repair QA, not PR merge or a production launch/security approval.
No source write, customer-data access, commit, push, merge, deployment,
external model call or external network request was performed by this agent.
The dependency emitted one Starlette/httpx deprecation warning per suite;
it did not skip or fail any test.
