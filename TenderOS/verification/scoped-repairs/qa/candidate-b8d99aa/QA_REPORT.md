# T-004 final independent QA

Candidate `b8d99aa32abab9e46147eaac7ce93cdbb32307d4` passed **153 tests**:
77 repository tests, the original frozen 33 independent cases, and the new
frozen 43 supplemental cases. All three suites had zero failures, errors or
skips. Candidate source hashes and HEAD remained unchanged, and the worktree
remained clean.

The 43 supplemental cases were also independently executed on a read-only
external `git archive` copy of prior candidate
`3cbcb46acd1ceb17d937d9c2bbc913ed44817485`, without checking out or modifying
the shared worktree. That negative control produced 34 passes and nine
failures, with zero errors or skips: equivalent float `1.0` and bool `True`
attestation IDs incorrectly left BID current, and each of the seven Excel
error codes became error cells. All nine now pass on the final candidate.
The 34 previously passing supplemental cases remain passing.

The original first-candidate 85-pass receipt and frozen 33-case harness were
preserved byte for byte. Their initial acceptance is supplemented by this
new negative-control evidence and final candidate results.

Supplemental QA confirms nested attestation floats, bools, strings, null,
lists, dictionaries, missing fields, extra fields and invalid enclosing types
fail closed without crashing GET or report exports and without rewriting
historical rows. Every openpyxl-recognized Excel error code, eight additional
modern Excel codes, five numeric-looking text values and four plain/Unicode
values remain exact string cells across title, matrix and reviewer/rationale
history fields. Actual numeric requirement IDs and page values remain numeric.
The original 33 cases continue covering source/evidence invalidation,
re-attestation, immutable history, legacy snapshots and formula prefixes.

A read-only diff review confirmed the minimal follow-up uses exact nested
attestation keys, exact Python value types and values, and explicitly assigns
string cell types throughout the generated workbook. No actionable defect was
found within the bounded repair scope.

Exact executions:

```text
/workspace/.venvs/tenderos-baseline/bin/python /workspace/tenderos-independent-qa/run_supplemental_qa.py --source /workspace/tenderos-fix/TenderOS --expected-commit b8d99aa32abab9e46147eaac7ce93cdbb32307d4 --label candidate-b8d99aa
/workspace/.venvs/tenderos-baseline/bin/python /workspace/tenderos-independent-qa/run_prior_supplemental.py
```

The nested suite argv, UTC times, source hashes, results and original-suite
receipt location are in `result.json`; prior negative-control failures and
archived-source preservation are in
`../prior-supplemental-3cbcb46/result.json`. Captured stdout/stderr, JUnit XML,
request traces and artifact SHA256 manifests accompany both runs. Original
repository/frozen-harness execution details are under
`../candidate-b8d99aa-original/`.

Actual tool chunks: `cdbbf7` final-candidate launch, `7bc4c3` completion;
`b8a556` archived-prior launch, `de9426` completion; `18e734` read-only diff
and postflight; `20c14a` comparison/hash inspection. Runtime task identity is
`/root/tenderos_patch_qa`; no separate opaque runtime run ID was exposed or
invented. No source edit, customer data access, external network/model call,
commit, push, merge or deployment was performed by this QA agent. These
results establish the bounded repair QA outcome, not production approval.
