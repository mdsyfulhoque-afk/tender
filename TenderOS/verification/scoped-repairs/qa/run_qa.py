"""Capture independent QA evidence outside any TenderOS checkout."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
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


def source_manifest(source):
    return {str(p.relative_to(source)): digest(p) for directory in ("app", "tests")
            for p in sorted((source / directory).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--with-original-suite", action="store_true")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = ROOT / args.label
    output.mkdir()
    started = utc()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, text=True,
                         capture_output=True, check=True).stdout.strip()
    assert sha == args.expected_commit, (sha, args.expected_commit)
    before = source_manifest(source)
    environment = os.environ.copy()
    environment.update({"TENDEROS_QA_SOURCE": str(source), "TENDEROS_DATA_DIR": str(output / "original-import-data"),
                        "TENDEROS_QA_REQUEST_TRACE": str(output / "request-trace.json"),
                        "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    suites = [("independent", str(ROOT / "test_independent_repairs.py"))]
    if args.with_original_suite:
        suites.insert(0, ("repository", str(source / "tests")))
    results = []
    for name, suite in suites:
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", suite,
                   "--basetemp=" + str(output / (name + "-tmp")),
                   "--junitxml=" + str(output / (name + ".xml"))]
        execution_start = utc()
        execution = subprocess.run(command, cwd=source, env=environment,
                                   capture_output=True, text=True, timeout=120)
        (output / (name + ".stdout.txt")).write_text(execution.stdout)
        (output / (name + ".stderr.txt")).write_text(execution.stderr)
        junit = ET.parse(output / (name + ".xml")).getroot()
        testsuites = list(junit.iter("testsuite"))
        counts = {key: sum(int(item.attrib.get(key, "0")) for item in testsuites)
                  for key in ("tests", "failures", "errors", "skipped")}
        failures = [{"test": case.attrib["name"], "message": failure.attrib.get("message"),
                     "details": failure.text}
                    for case in junit.iter("testcase")
                    for failure in case if failure.tag in ("failure", "error")]
        results.append({"suite": name, "command_argv": command, "cwd": str(source),
                        "start_utc": execution_start, "end_utc": utc(), "exit_code": execution.returncode,
                        "counts": counts, "failures": failures})
    after = source_manifest(source)
    versions = {package: importlib.metadata.version(package) for package in
                ("fastapi", "pydantic", "starlette", "httpx", "pytest", "openpyxl", "pypdf", "reportlab")}
    result = {"task_id": "T-004", "canonical_agent_id": "/root/tenderos_patch_qa",
              "runtime": "Codex collaboration spawned subagent", "delegation_tool": "collaboration.spawn_agent",
              "opaque_run_id": None, "opaque_run_id_status": "No separate opaque runtime run ID is exposed; no ID invented",
              "preparation_observed_utc": "2026-10-09T16:22:24Z", "start_utc": started, "end_utc": utc(),
              "source": str(source), "source_commit": sha,
              "qa_harness_sha256": digest(ROOT / "test_independent_repairs.py"),
              "qa_runner_sha256": digest(Path(__file__)), "python": sys.version,
              "dependencies": versions, "suites": results,
              "source_hashes_before": before, "source_hashes_after": after,
              "source_unchanged": before == after, "data": "synthetic only",
              "application_source_modified": False, "existing_customer_database_read": False,
              "external_network_calls": False, "external_model_api_calls": False,
              "commit_push_merge_deploy": False,
              "environment_overrides": {key: environment[key] for key in
                ("TENDEROS_QA_SOURCE", "TENDEROS_DATA_DIR", "TENDEROS_QA_REQUEST_TRACE", "PYTHONDONTWRITEBYTECODE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD")},
              "tool_traces_location": "Codex conversation tool trace for canonical task /root/tenderos_patch_qa; external command evidence in this report directory",
              "preparation_execution_chunks": ["6704b6", "289b62", "664a73", "25be70", "05a42c"],
              "all_passed": before == after and all(x["exit_code"] == 0 and x["counts"]["skipped"] == 0 for x in results),
              "execution_response_chunk": "Available to parent after this process finishes; not invented here"}
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    artifacts = {str(p.relative_to(output)): digest(p) for p in sorted(output.glob("*")) if p.is_file()}
    (output / "artifact-hashes.json").write_text(json.dumps(artifacts, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "all_passed": result["all_passed"], "source_unchanged": before == after,
                      "suites": [{"suite": item["suite"], "counts": item["counts"], "exit_code": item["exit_code"]} for item in results]}, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
