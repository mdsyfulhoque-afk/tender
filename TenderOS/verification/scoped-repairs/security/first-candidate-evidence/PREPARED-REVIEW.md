# TenderOS independent security review preparation

Prepared at 2026-10-09T16:23:28Z by actual canonical task `/root/tenderos_patch_security`, dispatched with `collaboration.spawn_agent`. Separate opaque runtime run IDs are not exposed and are not claimed. Tool calls and outputs are retained in this task's runtime transcript. The strict historical receipt gate remains unmet.

Read-only baseline: `/workspace/tender` at `ca819a902f5f8ac1bc18b10238505c3cd773cca6`. Candidate source will be read only after the parent supplies a completed commit.

## Findings guiding adversarial verification

- Baseline decision currency ignores stored `scope_hash`, allowing a zero-candidate source addendum to leave an old BID current. Re-attesting changed sources must not reactivate an old approval.
- Baseline requirement fingerprint omits linked evidence label, reference, expiry date, verification note and verification flag when effective status does not change. These values are part of the evidence the reviewer assessed. There is no evidence-edit API; direct SQLite mutations in a synthetic disposable fixture will test stored-state behavior without claiming a remotely reachable exploit.
- Requirement source linkage (`source_id`) and status rationale (`notes`) are absent from both relevant fingerprint projections. Source inventory identity/content and linked requirement provenance need coherent coverage.
- Legacy or malformed decision JSON must remain readable as historical data without becoming current or crashing all read/export paths.
- Latest-only decision selection must prevent an older approval resurfacing when the latest decision becomes stale. Unlinked evidence and unrelated tender activity must not invalidate another assessment.
- Parent clarified the bounded requirement on 2026-10-09: a new source-scope attestation must invalidate an earlier BID even when its scope and timestamp are unchanged. The existing `human_source_scope_attested` audit event identity will provide that revision; unrelated audit events and pilot metrics must have no effect.
- XLSX protection must cover all dynamic strings in both worksheets, especially title and decision reviewer/rationale, not only matrix rows. Harmless `=1+1`, plus/minus/at prefixes, leading whitespace, Unicode text and ordinary values will be checked as literal strings without formula evaluation.
- Export safety changes must leave numeric IDs/page numbers numeric and preserve layout and non-dangerous values. Historical SQLite rows and original snapshot strings must remain unchanged by read, rejection or export operations.

The review is confined to these repairs, synthetic local data, independent harness/log/report files in `/workspace/tenderos-independent-security`, and read-only Git/source inspection. It does not certify public deployment, identity/tenant isolation, an AI gateway or the complete product.
