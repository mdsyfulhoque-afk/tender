"""Run frozen original and separate supplemental QA against an immutable SHA."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(source):
    return {str(p.relative_to(source)): digest(p) for folder in ("app", "tests")
            for p in sorted((source / folder).rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def head(source):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, check=True,
                          capture_output=True, text=True).stdout.strip()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = ROOT / args.label
    output.mkdir()
    assert head(source) == args.expected_commit
    before = manifest(source)
    initial_harness_sha = "840f3438973fdd4d18579c44ca3fcab98276fe0f7ec49ada131e8493289b752d"
    assert digest(ROOT / "test_independent_repairs.py") == initial_harness_sha
    first_receipt = ROOT / "candidate-3cbcb46/completion-receipt.json"
    assert digest(first_receipt) == "841bdc829e655ac753043f18e286896440e596a16a22793516e5d66e712def29"
    started = utc()
    original_label = args.label + "-original"
    original_command = [sys.executable, str(ROOT / "run_qa.py"), "--source", str(source),
                        "--expected-commit", args.expected_commit, "--label", original_label, "--with-original-suite"]
    original = subprocess.run(original_command, capture_output=True, text=True, timeout=120)
    (output / "original-runner.stdout.txt").write_text(original.stdout)
    (output / "original-runner.stderr.txt").write_text(original.stderr)
    original_result = json.loads((ROOT / original_label / "result.json").read_text())
    assert head(source) == args.expected_commit and manifest(source) == before, "STOP: source changed during original suites"
    env = os.environ.copy()
    env.update({"TENDEROS_QA_SOURCE": str(source), "TENDEROS_DATA_DIR": str(output / "module-import-data"),
                "TENDEROS_QA_REQUEST_TRACE": str(output / "supplemental-request-trace.json"),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(ROOT / "test_supplemental_repairs.py"),
               "--basetemp=" + str(output / "supplemental-tmp"), "--junitxml=" + str(output / "supplemental.xml")]
    supplemental_start = utc()
    supplemental = subprocess.run(command, cwd=source, env=env, capture_output=True, text=True, timeout=120)
    (output / "supplemental.stdout.txt").write_text(supplemental.stdout)
    (output / "supplemental.stderr.txt").write_text(supplemental.stderr)
    junit = ET.parse(output / "supplemental.xml").getroot()
    counts = {key: sum(int(suite.attrib.get(key, "0")) for suite in junit.iter("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    failures = [{"test": case.attrib["name"], "message": failure.attrib.get("message"), "details": failure.text}
                for case in junit.iter("testcase") for failure in case if failure.tag in ("failure", "error")]
    after = manifest(source)
    final_head = head(source)
    stable = final_head == args.expected_commit and before == after
    all_passed = original.returncode == 0 and supplemental.returncode == 0 and counts["skipped"] == 0 and stable
    receipt = {"task_id": "T-004 supplemental independent QA", "canonical_agent_id": "/root/tenderos_patch_qa",
               "opaque_run_id": None, "opaque_run_id_status": "No separate opaque run ID exposed; none invented",
               "start_utc": started, "end_utc": utc(), "source": str(source), "expected_commit": args.expected_commit,
               "final_head": final_head, "source_hashes_before": before, "source_hashes_after": after,
               "source_stable": stable, "all_passed": all_passed,
               "original_harness_sha256": initial_harness_sha,
               "supplemental_harness_sha256": digest(ROOT / "test_supplemental_repairs.py"),
               "supplemental_runner_sha256": digest(Path(__file__)),
               "first_candidate_receipt_unchanged": digest(first_receipt) == "841bdc829e655ac753043f18e286896440e596a16a22793516e5d66e712def29",
               "original_suites_receipt": str(ROOT / original_label / "result.json"),
               "original_suites_receipt_sha256": digest(ROOT / original_label / "result.json"),
               "original_suites": original_result["suites"], "original_runner_command_argv": original_command,
               "supplemental_suite": {"start_utc": supplemental_start, "command_argv": command,
                                      "counts": counts, "exit_code": supplemental.returncode, "failures": failures},
               "data_egress": "None; synthetic in-process TestClient requests only",
               "application_source_modified": False, "customer_data_read": False,
               "network_model_calls": False, "commit_push_merge_deploy": False,
               "execution_response_chunk": "Parent captures actual response after completion; no fabricated trace ID"}
    (output / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    artifacts = {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}
    (output / "artifact-hashes.json").write_text(json.dumps(artifacts, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "all_passed": all_passed, "source_stable": stable,
                      "original_suites": [{"suite": x["suite"], "counts": x["counts"]} for x in original_result["suites"]],
                      "supplemental": counts}, indent=2))
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(run())
