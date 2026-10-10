#!/usr/bin/env python3
# capture_preservation.py -- capture the implementer Git/worktree baseline snapshot
# for G_PRESERVE (TASK-20261010-catalog-diagnostic-continuity-replan).
#
# Read-only: it only reads files and runs git plumbing commands, and writes the
# snapshot to a new exclusive file.

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
TASK = os.path.join(ROOT, "harness-development", "catalog-diagnostic-continuity-replan-20261010")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    proc = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def list_files(rel_dir):
    out = {}
    base = os.path.join(ROOT, rel_dir)
    for dirpath, _, files in os.walk(base):
        for name in sorted(files):
            if name == ".DS_Store":
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT)
            out[rel] = sha256_file(path)
    return out


def capture(role):
    rc_head, head, _ = git("rev-parse", "HEAD")
    rc_branch, branch, _ = git("branch", "--show-current")
    rc_status, status, _ = git("status", "--porcelain=v1")
    rc_diff, diff, _ = git("diff")
    rc_cached, cached, _ = git("diff", "--cached")
    _, ls_files, _ = git("ls-files")
    tracked = sorted(line for line in ls_files.splitlines() if line)
    untracked = sorted(line.split("\t", 1)[-1].strip().strip('"')
                       for line in status.splitlines() if line.startswith("??"))
    index_path = os.path.join(ROOT, ".git", "index")

    snapshot = {
        "format": "local-preservation-snapshot-1",
        "role": role,
        "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
        "project_root": ROOT,
        "git": {
            "head": head.strip(),
            "branch": branch.strip(),
            "status_porcelain": status.splitlines(),
            "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
            "diff_bytes": len(diff.encode("utf-8")),
            "diff_cached_sha256": hashlib.sha256(cached.encode("utf-8")).hexdigest(),
            "diff_cached_bytes": len(cached.encode("utf-8")),
            "index_sha256": sha256_file(index_path) if os.path.isfile(index_path) else None,
            "tracked_count": len(tracked),
            "untracked_count": len(untracked),
            "tracked_sha256": hashlib.sha256("\n".join(tracked).encode("utf-8")).hexdigest(),
            "untracked_sha256": hashlib.sha256("\n".join(untracked).encode("utf-8")).hexdigest(),
            "untracked_paths": untracked,
        },
        "canonical_state": {
            rel: sha256_file(os.path.join(ROOT, rel))
            for rel in ("config/line_backup_config.json", "state/backup_state.json", "state/run_log.md")
            if os.path.isfile(os.path.join(ROOT, rel))
        },
        "old_diagnostic_task": list_files("harness-development/catalog-diagnostic-20261010"),
        "backups": list_files("backups"),
        "product_sources": {
            rel: sha256_file(os.path.join(ROOT, rel))
            for rel in (tracked + untracked)
            if rel.startswith(("src/", "rev28/")) and os.path.isfile(os.path.join(ROOT, rel))
        },
        "task_frozen_documents": {
            rel: sha256_file(os.path.join(ROOT, "harness-development",
                                          "catalog-diagnostic-continuity-replan-20261010", rel))
            for rel in ("handoff.md", "diagnostic-spec.json", "plan-contract.json", "handoff.json",
                        "authorization.json", "source-manifest.json", "plan-as-submitted.md",
                        "plan-review-01.result.json", "plan-review-01.pixel-probe.log",
                        "plan-review-01.schema-validation.json")
            if os.path.isfile(os.path.join(ROOT, "harness-development",
                                           "catalog-diagnostic-continuity-replan-20261010", rel))
        },
        "implementation_scope": list_files("harness-development/catalog-diagnostic-continuity-replan-20261010"),
    }
    return snapshot


def main():
    role = sys.argv[1]
    out_path = sys.argv[2]
    snapshot = capture(role)
    if os.path.exists(out_path):
        raise SystemExit(f"OUTPUT_EXISTS: {out_path}")
    with open(out_path, "xb") as fh:
        fh.write(json.dumps(snapshot, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    print(json.dumps({"out": out_path, "head": snapshot["git"]["head"],
                      "files": len(snapshot["implementation_scope"])}))


if __name__ == "__main__":
    main()
