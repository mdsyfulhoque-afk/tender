# TenderOS independent bounded security verification

Verdict: PASS for the two authorized local repairs at immutable candidate `b8d99aa32abab9e46147eaac7ce93cdbb32307d4`. Independent adversarial checks passed **81/81**, with zero skips or failures: 37 core checks and 44 expanded edge checks. This verdict covers decision currency and literal XLSX exports only.

## Verified behavior

- A zero-candidate addendum, changed source content/provenance/linkage, changed linked evidence or changed status rationale invalidates an old BID without rewriting historical rows.
- Re-attestation with identical scope and timestamp invalidates the old BID through the attestation audit event identity. Unrelated metrics, evidence and tender activity do not invalidate it.
- Missing, malformed, legacy or incorrectly typed decision metadata remains historical. Float/bool/string/null/list/dict audit identifiers, missing/extra attestation fields and wrong reviewer/note/time/hash types cannot match current metadata.
- Evidence expiry invalidates current BID with no database write. Latest-only selection prevents an older BID from resurfacing. HOLD and NO_BID can remain current when mandatory readiness is unresolved.
- Every XLSX string cell is serialized as literal text, including all seven openpyxl Excel error tokens, newer error-looking strings, numeric-looking strings, benign formula prefixes, actual leading tab/CRLF/NBSP whitespace, BOM/zero-width prefixes, Bengali text and ordinary literals. Exact escaped values are checked. Requirement IDs and source pages remain numeric. No formula XML cells or external workbook links were produced; no formula was evaluated.
- GET, rejected BID attempts and exports preserve stored decision rows/snapshot content. Synthetic fixtures explicitly mutate stored data only to construct the adversarial starting states.

The earlier candidate `3cbcb46` was not accepted. Its three observed failures—floating attestation identity plus `#N/A` and `#VALUE!` error cells—are now resolved. Original findings, results, request traces and harness files remain in `first-candidate-evidence/` and `INITIAL-CANDIDATE-REVIEW.md`.

## Source and execution evidence

Actual canonical task: `/root/tenderos_patch_security`, separately launched through `collaboration.spawn_agent`. This agent independently reviewed the frozen two-file change and authored the security harnesses. Separate opaque runtime run IDs are not exposed and remain null; the original strict historical receipt gate is not declared passed.

Verified before and after execution:

- HEAD: `b8d99aa32abab9e46147eaac7ce93cdbb32307d4`, worktree clean.
- Application SHA-256: `816183fdbd34acbeff18c3a08061adaeef43191b0e9615f1df4dd2c2f82609e0`.
- Candidate tests SHA-256: `087dfc61ffedcee1ea5c89a43416f27f70317152de93e28bd07125e899001d38`.

Commands:

```text
git -C /workspace/tenderos-fix diff 3cbcb46 b8d99aa -- TenderOS/app/main.py TenderOS/tests/test_workflows.py
python /workspace/tenderos-independent-security/adversarial_review.py --source /workspace/tenderos-fix --commit b8d99aa32abab9e46147eaac7ce93cdbb32307d4 --additional-metadata currency_version scope_attestation
python /workspace/tenderos-independent-security/security_edges.py --commit b8d99aa32abab9e46147eaac7ce93cdbb32307d4
```

Actual runtime transcript chunk IDs: follow-up diff `fd0a66`, initial hashes/time `9e7c98`, initial evidence preservation `b048ff`, core dispatch `62e105`, expanded edge dispatch `4b1aa1`, core completion `ed9e95`, edge completion `248033`, counts/final source hashes `54a1a3`. These are actual tool trace identifiers, not opaque agent run IDs.

Results, timestamps and synthetic HTTP traces: `security-results.json`, `security-edge-results.json`, `synthetic-request-trace.json`, `synthetic-edge-request-trace.json`. Exact commands' stdout/stderr are retained in the corresponding `security*.txt` logs. The only stderr output is the installed Starlette/httpx deprecation warning; both processes exited 0. Artifact hashes are recorded in `security-output-hashes.json`.

All data is synthetic; writes are confined to `/workspace/tenderos-independent-security`; no application edits, Git commits, external requests, model calls, credential use, merge, push or deployment were performed by this agent. The known identity/tenant isolation and public rollout gaps are outside this repair and are not certified by this verdict.
