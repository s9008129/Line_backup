#!/usr/bin/env python3
# make_preservation_delta.py -- compare two preservation snapshots and write the
# delta (exclusive create). Read-only with respect to the compared snapshots.
import json
import os
import sys


def load(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def diff_map(before, after):
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return {"added": added, "changed": changed, "removed": removed,
            "count_before": len(before), "count_after": len(after)}


def main():
    before_path, after_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    before, after = load(before_path), load(after_path)
    gb, ga = before["git"], after["git"]
    untracked_before = sorted(gb.get("untracked_paths", []))
    untracked_after = sorted(ga.get("untracked_paths", []))
    added_untracked = [p for p in untracked_after if p not in set(untracked_before)]
    removed_untracked = [p for p in untracked_before if p not in set(untracked_after)]
    protected = {}
    for key in ("canonical_state", "old_diagnostic_task", "backups",
                "product_sources", "task_frozen_documents"):
        protected[key] = diff_map(before.get(key, {}), after.get(key, {}))
    changed_protected = any(protected[k]["added"] or protected[k]["changed"]
                            or protected[k]["removed"] for k in protected)
    git_ok = (gb.get("head") == ga.get("head") and gb.get("branch") == ga.get("branch")
              and gb.get("index_sha256") == ga.get("index_sha256")
              and gb.get("diff_sha256") == ga.get("diff_sha256")
              and gb.get("diff_cached_sha256") == ga.get("diff_cached_sha256"))
    delta = {
        "format": "local-preservation-delta-1",
        "task_id": before.get("task_id"),
        "before_head": gb.get("head"),
        "after_head": ga.get("head"),
        **protected,
        "implementation_scope": diff_map(before.get("implementation_scope", {}),
                                         after.get("implementation_scope", {})),
        "git": {
            "branch_changed": gb.get("branch") != ga.get("branch"),
            "head_changed": gb.get("head") != ga.get("head"),
            "index_changed": gb.get("index_sha256") != ga.get("index_sha256"),
            "tracked_diff_changed": gb.get("diff_sha256") != ga.get("diff_sha256"),
            "cached_diff_changed": gb.get("diff_cached_sha256") != ga.get("diff_cached_sha256"),
            "untracked_added": added_untracked,
            "untracked_removed": removed_untracked,
            "untracked_paths_changed": bool(added_untracked or removed_untracked),
        },
        "preservation_verdict": "PASS" if (git_ok and not changed_protected) else "FAIL",
    }
    if os.path.exists(out_path):
        raise SystemExit("OUTPUT_EXISTS: " + out_path)
    with open(out_path, "xb") as fh:
        fh.write(json.dumps(delta, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")
    print(json.dumps({"out": out_path, "verdict": delta["preservation_verdict"],
                      "scope_added": len(delta["implementation_scope"]["added"]),
                      "scope_changed": len(delta["implementation_scope"]["changed"])}))


if __name__ == "__main__":
    main()
