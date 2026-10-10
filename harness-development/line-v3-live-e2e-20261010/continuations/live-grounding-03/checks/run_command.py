#!/usr/bin/env python3
"""Run one frozen local check and retain its exact invocation and byte streams."""
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent.parent
REPO_ROOT = HERE.parents[3]
EVIDENCE = HERE / "evidence"


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main():
    if len(sys.argv) < 3 or sys.argv[2] != "--":
        raise SystemExit("usage: run_command.py CHECK_ID -- COMMAND [ARG ...]")
    check_id = sys.argv[1]
    if not check_id.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("invalid check id")
    command = sys.argv[3:]
    if not command:
        raise SystemExit("empty command")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    invocation = {"check_id": check_id, "cwd": str(REPO_ROOT), "command": command,
                  "started_at": started}
    result = subprocess.run(command, cwd=REPO_ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    ended = utc_now()
    stem = EVIDENCE / check_id
    stem.with_suffix(".stdout").write_bytes(result.stdout)
    stem.with_suffix(".stderr").write_bytes(result.stderr)
    invocation["ended_at"] = ended
    invocation["exit_code"] = result.returncode
    (EVIDENCE / f"{check_id}.invocation.json").write_text(
        json.dumps(invocation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"format_version": "1", "check_id": check_id,
               "status": "PASS" if result.returncode == 0 else "FAIL",
               "exit_code": result.returncode, "started_at": started, "ended_at": ended,
               "stdout": {"path": f"{HERE.relative_to(REPO_ROOT)}/evidence/{check_id}.stdout",
                          "bytes": len(result.stdout),
                          "sha256": hashlib.sha256(result.stdout).hexdigest()},
               "stderr": {"path": f"{HERE.relative_to(REPO_ROOT)}/evidence/{check_id}.stderr",
                          "bytes": len(result.stderr),
                          "sha256": hashlib.sha256(result.stderr).hexdigest()}}
    (EVIDENCE / f"{check_id}.receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
