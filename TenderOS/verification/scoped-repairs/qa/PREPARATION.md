# Independent T-004 QA preparation

Canonical runtime task: `/root/tenderos_patch_qa`. Preparation read only the
immutable imported source at commit `ca819a902f5f8ac1bc18b10238505c3cd773cca6`
in `/workspace/tender/TenderOS` and its recorded baseline reproductions. No
candidate source was read during preparation.

The independent harness currently contains 33 parameterized cases. It checks
zero-candidate addenda, changed requirement/source association, changed source
content hashes, linked evidence identity and metadata changes, evidence
revocation and expiry, source re-attestation including identical timestamps,
legacy stored decisions, immutable historical rows, unrelated evidence,
metrics and export reads, unchanged no-op requirement reviews, explicit HOLD
and NO_BID in unresolved states, and XLSX title/history/matrix strings with
four formula-like prefixes and four leading whitespace variants. Numeric
spreadsheet columns and historical snapshot text are also checked.

On the unmodified baseline, all 33 cases ran without skips or test errors:
21 passed and 12 failed. Failures reproduce the stale approval and unsafe
XLSX problems. The source hashes were identical before and after execution.
See `baseline/result.json`, `baseline/independent.xml`, captured stdout and
the synthetic in-process request trace.

Some metadata changes require direct writes to the isolated synthetic test
database because the current pilot exposes no evidence or source update API.
The expiry case advances the application's date with a test monkeypatch.
Spreadsheet strings are benign and no spreadsheet engine or formula
calculation runs. Leading whitespace is preserved in synthetic persisted
records because the API trims most such fields. Local TestClient exercises
the application in process; no external HTTP/model request is used.

All harness, runtime and receipt files are written beneath this directory.
Application and repository tests stay read only. No commit, push, merge,
deployment, existing customer database read, or external model use occurs.
No separate opaque run ID is exposed by this runtime; the canonical task
identity and actual tool traces are recorded without inventing an ID.

For a frozen candidate, run the existing external runner with its full
expected commit and `--with-original-suite`; choose a fresh label so the
runner refuses to overwrite an earlier report directory. Source/app hashes
are captured before and after both suites.
