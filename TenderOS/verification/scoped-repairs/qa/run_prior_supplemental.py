"""Record the frozen supplemental cases on an archived, read-only prior SHA."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
COMMIT = "3cbcb46acd1ceb17d937d9c2bbc913ed44817485"
SOURCE = ROOT / "prior-3cbcb46-source/TenderOS"
OUTPUT = ROOT / "prior-supplemental-3cbcb46"


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    return {str(p.relative_to(SOURCE)): sha(p) for p in sorted(SOURCE.rglob("*")) if p.is_file()}


def run():
    started = utc()
    OUTPUT.mkdir()
    SOURCE.parent.mkdir()
    extraction = subprocess.run(["git", "archive", "--format=tar", COMMIT, "TenderOS/app"],
                                cwd="/workspace/tenderos-fix", check=True, capture_output=True)
    archive_bytes = extraction.stdout
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        archive.extractall(SOURCE.parent, filter="data")
    assert sha(SOURCE / "app/main.py") == "5377bf1e87eff9e0641ceb5103b96aa1bad978690ab6551375bdb7189777b5b0"
    for path in SOURCE.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
    before = manifest()
    harness = ROOT / "test_supplemental_repairs.py"
    assert sha(harness) == "ea25ac65c87599f55a8e71c2377cae32ad682d492e607fb68a0a298d40b94a7e"
    env = os.environ.copy()
    env.update({"TENDEROS_QA_SOURCE": str(SOURCE), "TENDEROS_DATA_DIR": str(OUTPUT / "module-import-data"),
                "TENDEROS_QA_REQUEST_TRACE": str(OUTPUT / "request-trace.json"),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(harness),
               "--basetemp=" + str(OUTPUT / "tmp"), "--junitxml=" + str(OUTPUT / "supplemental.xml")]
    execution = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True, text=True, timeout=120)
    (OUTPUT / "supplemental.stdout.txt").write_text(execution.stdout)
    (OUTPUT / "supplemental.stderr.txt").write_text(execution.stderr)
    junit = ET.parse(OUTPUT / "supplemental.xml").getroot()
    counts = {key: sum(int(suite.attrib.get(key, "0")) for suite in junit.iter("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    failures = [{"test": case.attrib["name"], "message": failure.attrib.get("message"), "details": failure.text}
                for case in junit.iter("testcase") for failure in case if failure.tag in ("failure", "error")]
    after = manifest()
    receipt = {"task_id": "T-004 supplemental before-change reproduction", "canonical_agent_id": "/root/tenderos_patch_qa",
               "source_commit": COMMIT, "source": str(SOURCE), "source_method": "git archive to external staging; no checkout or worktree mutation",
               "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
               "harness_sha256": sha(harness), "start_utc": started, "end_utc": utc(),
               "command_argv": command, "cwd": str(SOURCE), "exit_code": execution.returncode,
               "counts": counts, "failures": failures,
               "source_hashes_before": before, "source_hashes_after": after, "source_unchanged": before == after,
               "opaque_run_id": None, "opaque_run_id_status": "No separate opaque run ID exposed; none invented",
               "data_egress": "None; synthetic in-process requests only", "application_source_modified": False,
               "customer_data_read": False, "network_model_calls": False, "commit_push_merge_deploy": False}
    (OUTPUT / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    artifact_hashes = {p.name: sha(p) for p in sorted(OUTPUT.iterdir()) if p.is_file()}
    (OUTPUT / "artifact-hashes.json").write_text(json.dumps(artifact_hashes, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUTPUT), "counts": counts, "source_unchanged": before == after,
                      "before_change_failures_reproduced": counts["failures"] > 0 and counts["errors"] == 0 and counts["skipped"] == 0}, indent=2))
    # Expected negative-control failures are a successful reproduction.
    return 0 if before == after and counts["failures"] > 0 and counts["errors"] == 0 and counts["skipped"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
