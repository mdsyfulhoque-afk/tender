# Independent final QA report

## Scope and identity

- QA agent: `/root/final_independent_qa`.
- Worktree: `/workspace/tenderos-agent-workbench`, branch `tenderos/agent-workbench`.
- Baseline commit: `6f7ac1156e595f9f87d6f32d99492f8a704e9849`.
- Opaque platform run ID and exported tool trace ID: `null` (not exposed by this execution environment).
- No paid API/model/provider or production data was used. A later independent access check against the GitHub/Vercel-created preview was denied by deployment protection before origin access; no application endpoint was reached. All database checks used fresh `TENDEROS_DATA_DIR` directories; the repository/default database was not opened or modified.
- QA made no application-source edits. QA added the independent test file and this report. The requested trailing-whitespace cleanup in `tests/test_workflows.py` leaves no diff there.

## Results

The independent direct-handler integration harness passed all 3 tests. It exercises a synthetic PDF through the durable four-stage RULES workflow; candidate acceptance only into `UNKNOWN`/unreviewed state; subsequent ordinary domain gates; commercial intake, release and exports; and ledger receipt, cost, partial refund, reversal, stale/immutable behavior, permissions, and prompt-injection boundaries. The harness uses local synthetic data and verifies no model/provider execution.

The remaining isolated non-HTTP suite passed **73 tests**. This covers the independent harness plus workflow contracts, schema/migration behavior, canonical JSON/page bounds, aggregate receipt budget, historical currency limits, and related regressions. Two focused commercial tests passed separately, including DOCX control-character handling and repeat/digest drift behavior.

The full pytest suite did not complete: it collected 197 tests, passed the first 12, then stalled at `tests/test_commercial_operations.py::test_blank_intake_and_quote_do_not_count_as_cash`. A 12-second timeout ended that attempt with exit code 124. The stall was independently reproduced using a trivial FastAPI endpoint with `TestClient`, `httpx.ASGITransport`, and a direct ASGI callable; the stack blocked in `anyio.from_thread.portal.call` while the event loop was idle. Starlette also emitted its `httpx`/`TestClient` deprecation warning. This indicates a local HTTP test-transport/environment issue, but does not establish that the HTTP middleware/request path works. The following files were omitted from the 73-test passing command because they contain the stalled TestClient path:

- `tests/test_workflows.py`
- `tests/test_commercial_operations.py`

Their important product flows were separately exercised by direct calls to the registered route handlers in the independent integration harness. This is not equivalent to a passing HTTP end-to-end run.

Static checks passed: JavaScript syntax (`node --check app/static/ui.js`), Python compilation (`compileall` over `app`, `scripts`, and `tests`), and `git diff --check`. Chromium/browser rendering and interaction were not tested.

## Exact commands and isolated data directories

Commands were run from `/workspace/tenderos-agent-workbench/TenderOS` with `/workspace/.venvs/tenderos-baseline/bin/python`.

```sh
TENDEROS_DATA_DIR=/tmp/tenderos-independent-qa-20261010-12 \
/workspace/.venvs/tenderos-baseline/bin/python -m pytest -q tests/test_agent_workbench_independent.py
# 3 passed in 0.75s; one Starlette TestClient/httpx deprecation warning.

TENDEROS_DATA_DIR=/tmp/tenderos-independent-qa-20261010-17 \
/workspace/.venvs/tenderos-baseline/bin/python -m pytest -q \
  --ignore=tests/test_workflows.py --ignore=tests/test_commercial_operations.py
# 73 passed in 1.45s; same deprecation warning.

TENDEROS_DATA_DIR=/tmp/tenderos-independent-qa-20261010-14 \
/workspace/.venvs/tenderos-baseline/bin/python -m pytest -q \
  tests/test_commercial_operations.py::test_v4_fresh_repeat_digest_drift_and_unversioned_refusal \
  tests/test_commercial_operations.py::test_word_xml_controls_have_visible_markers_without_changing_snapshot
# 2 passed in 0.70s.

TENDEROS_DATA_DIR=/tmp/tenderos-independent-qa-20261010-16 \
timeout 12s /workspace/.venvs/tenderos-baseline/bin/python -m pytest -vv -x
# 197 collected; 12 passed before the TestClient stall above; exit 124.

node --check app/static/ui.js
TENDEROS_DATA_DIR=/tmp/tenderos-independent-qa-20261010-18 \
/workspace/.venvs/tenderos-baseline/bin/python -m compileall -q app scripts tests
git diff --check
# All three static/diff checks passed.
```

The separate TestClient transport reproduction was run on a trivial synthetic FastAPI endpoint, without network access. The final candidate is not certified as a complete passing 197-test suite because of this stall.

## Hosted preview access observation

The Vercel integration created a deployment marked **READY** for commit `eb4280b`: [preview URL](https://tender-git-tenderos-agent-workbench-ip-3.vercel.app). An independent QA fetch was denied with `403 Forbidden` at stage `read_protection_bypass`, before origin access. That protected fetch did not verify the application response or observe an HTTP root, rendered UI, API, database, or private file storage.

### Later user screenshot and root-entrypoint shim

The earlier user-provided screenshot of the preview URL showed Vercel `404 NOT_FOUND`. Later Vercel metadata confirmed deployment `dpl_GK3kcXCeGoDQVzLaL4gtCXZn8AZc` **READY** for commit `2f38991d`, assigning the exact branch alias `tender-git-tenderos-agent-workbench-ip-3.vercel.app`. `rootDirectory` had been reset to `null` (repository root) before this deployment, so it used root `vercel.json`, `.vercelignore`, and `pyproject.toml`. This READY status does not verify origin behavior: `web_fetch_vercel_url` still returns `403 Forbidden` at stage `read_protection_bypass`, before origin access. No HTTP root, UI, API, database, or private file storage was observed. Vercel metadata reads for `get_project`, `get_deployment`, and `list_deployments` succeed without `teamId`; explicit `teamId` calls fail with `403 Forbidden` in scope `ip-3`. The non-decrypting Vercel environment listing returned an empty list: no project environment variables are configured, so required database, private Blob and owner-auth settings are absent. Earlier build failures remain: `49777a4`, deployment `dpl_6cWLZ1Fx7beUeybLbMrT7vCFnxXu`, exceeded the `excludeFiles` schema limit; `d544651` failed at `uv lock` before root `[project]` metadata existed; and `c2add27`, deployment `dpl_7WrL2foMKMa1asTbqmELADbNciJD`, failed with `FASTAPI_ENTRYPOINT_NOT_FOUND` while `rootDirectory` was temporarily `TenderOS`. This follow-up records the subsequent READY deployment only; no tests were rerun.

## Candidate identity

Candidate SHA-256: `601e96bb8f3a1b9456f302f2cb079bc7ceb3e473377a59418ccfa1373699e8e4`.

This digest sorts all 39 modified and untracked worktree files from `git status --porcelain=v1 -z --untracked-files=all`, excludes `TenderOS/verification/agent-workbench/qa/` to avoid self-reference, then hashes each repository-relative path, a NUL byte, the raw SHA-256 digest of that file's contents, and a newline. It identifies the uncommitted candidate at QA completion, not a commit.

Key file SHA-256 values:

```text
app/workflows.py                         b1a239494fb7b1ae9cb8fbfb706e575e30afbd778fd4f27c6c07287dd63d42d0
app/main.py                              da26ba8d838ce3bd33319e1b1956bada4e067db7b445e029c9e8da1f94ff30d9
app/commercial.py                        5276c66b625560843dd0b9a6d92b139d34cc708a04557e8230e04e92d8b241ad
app/static/ui.js                         ec7bd229b37c10dd3b4aae34c2ff20015a72b975b0b04c266c8eb64a51529df5
tests/test_agent_workbench_independent.py 5bca06e95af2ba4ec494517eae443fe9e85a8f43102af95868853edb3dd6ec92
```

### Post-QA formatting-only update

After the QA candidate was frozen, the QA agent removed one terminal LF byte from `tests/test_agent_workbench_independent.py`. The prior hash above is retained as the tested-at-QA hash; the current file SHA-256 is `6058a18fab8e6849800864510d7dbc7751016b4a7d11bc065048579ab5f7c037`. This was a one-byte EOF-LF trim only; test content is unchanged. No tests were rerun for this formatting-only edit. The QA-at-completion digest above remains historical; the current worktree candidate digest is recorded separately in [`build-manifest.json`](../build-manifest.json).

## Limitations

No managed PostgreSQL or private object-storage service was connected or tested. The Vercel project's environment listing is empty, so required database, private Blob and owner-auth settings are absent. Vercel metadata now confirms READY deployment `dpl_GK3kcXCeGoDQVzLaL4gtCXZn8AZc` for commit `2f38991d`, created after `rootDirectory` was reset to `null` (repository root). The earlier `49777a4`, `d544651`, and `c2add27` build errors are recorded above. The current READY status does not verify origin access: `web_fetch_vercel_url` remains blocked before origin, and no app HTTP/browser flow, accessibility review, database, private file-storage, or production environment validation was performed. The missing opaque runtime run/trace identifiers remain unverified against the repository's stricter agent-runtime evidence policy; they are reported as unavailable rather than inferred. The release gate remains incomplete. QA results do not certify deployment or establish revenue outcomes.
