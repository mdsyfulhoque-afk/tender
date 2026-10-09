# Initial candidate security review: additional repairs required

Actual independent canonical task: `/root/tenderos_patch_security`. A separate opaque runtime run ID is unavailable; no strict receipt gate or public deployment approval is claimed.

Reviewed immutable clean candidate `3cbcb46acd1ceb17d937d9c2bbc913ed44817485`, comparing its application/test diff to `ca819a902f5f8ac1bc18b10238505c3cd773cca6`. Inspection began 2026-10-09T16:30:40Z. Baseline application and candidate worktree were not edited by this security agent.

Application SHA-256: `5377bf1e87eff9e0641ceb5103b96aa1bad978690ab6551375bdb7189777b5b0`.
Candidate tests SHA-256: `d636814627614a150696c33394ccec88b19a94f9eb5af834612996b650614bda`.

## Results

The prepared independently authored harness passed 37/37 cases, including zero-candidate addenda, no revival after reattestation, changed linked evidence without changed effective status, changed requirement source/rationale, no invalidation from unrelated activity, fail-closed malformed/missing snapshots, complete formula-prefix coverage, literal history exports and preserved stored historical rows. This run was repeated with exact expected escaped value assertions and also passed 37/37.

Initial additional boundary checks passed 17/20 and found three failures requiring follow-up within the bounded repair:

1. A snapshot's `scope_attestation.event_id` changed from integer `7` to JSON floating value `7.0` still leaves `is_current: true` because Python dictionary equality treats them as equal. This is a malformed-type synthetic stored-state probe; there is no decision-update API or claimed remote attack.
2. The untrusted string `#N/A` becomes an Excel error cell (`data_type: e`) at `Compliance Matrix!B2` rather than a literal string.
3. The untrusted string `#VALUE!` behaves the same way. This demonstrates that formula-prefix escaping alone does not enforce literal XLSX text serialization for all strings.

No formulas were evaluated, no customer data was used and no external service/model calls occurred. Source HEAD and hashes remained unchanged after verification. Candidate `3cbcb46` is not accepted as completing the requested scope; parent has dispatched a bounded follow-up and the independent agent will wait for the next stable SHA.

## Real whitespace coverage

The harness contains Python string escapes that evaluate to actual whitespace, verified independently with `ast.literal_eval`. Tested leading character code points were space/tab/equal `[32, 9, 61]`, CR/LF/equal `[13, 10, 61]`, tab/plus `[9, 43, 49]` and NBSP/equal `[160, 61, 49]`. JSON tool output necessarily displays escaped representations. The repeat added exact value expectations to strengthen the original assertion.

## Evidence

- Initial run: `initial-security-results.json`, `initial-synthetic-request-trace.json`, `initial-security.stdout.txt`, `initial-security.stderr.txt`.
- Repeat with stronger exact-value assertions: `security-results.json`, `synthetic-request-trace.json`, `security.stdout.txt`, `security.stderr.txt`.
- Edge failures: `security-edge-results.json`, `synthetic-edge-request-trace.json`, `security-edges.stdout.txt`, `security-edges.stderr.txt`.
- Independently authored harnesses: `adversarial_review.py`, `security_edges.py`. The edge harness has been extended after the failure report for all seven openpyxl Excel error codes plus modern error-looking strings, bool/float/missing/extra/other-type attestation metadata, and needs the next candidate SHA supplied explicitly.

Commands executed:

```text
git -C /workspace/tenderos-fix diff ca819a9 3cbcb46 -- TenderOS/app/main.py TenderOS/tests/test_workflows.py
python /workspace/tenderos-independent-security/adversarial_review.py --source /workspace/tenderos-fix --commit 3cbcb46acd1ceb17d937d9c2bbc913ed44817485 --additional-metadata currency_version scope_attestation
python /workspace/tenderos-independent-security/security_edges.py
```

Actual transcript chunk IDs include source diff `85dc97`, initial hashes `c8f4f6`, prepared harness dispatch `70b472`, boundary dispatch `447688`, observed failures `f7469c`, whitespace AST verification `9a33e7`, repeat dispatch `d7c14e`, repeat output/final hashes `fbec59`. These are tool trace chunk identifiers, not substituted opaque run IDs.
