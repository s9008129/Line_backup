#!/usr/bin/env python3
"""Independent read-back verifier for an evidence tree.

Re-reads every manifest.json found under the given root, recomputes SHA-256 and
byte length for each listed artifact, and reports mismatches, missing files and
uncovered files. Read-only: never writes into the evidence tree.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import sha256_bytes


def verify(root: Path) -> dict:
    manifests = sorted([m for m in root.rglob("*.manifest.json")] + [m for m in root.rglob("manifest.json") if not m.name.endswith(".manifest.json")])
    problems = []
    covered = set()
    checked = 0
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append({"manifest": str(manifest_path), "problem": f"unreadable manifest: {exc}"})
            continue
        base = manifest_path.parent
        for artifact in manifest.get("artifacts", []):
            rel = artifact.get("path")
            if rel is None:
                continue
            target = (base / rel).resolve()
            covered.add(str(target))
            checked += 1
            if not target.is_file():
                problems.append({"manifest": str(manifest_path), "path": rel, "problem": "missing"})
                continue
            data = target.read_bytes()
            if len(data) != artifact.get("bytes"):
                problems.append({"manifest": str(manifest_path), "path": rel, "problem": "byte-length mismatch",
                                 "expected": artifact.get("bytes"), "actual": len(data)})
            digest = sha256_bytes(data)
            if digest != artifact.get("sha256"):
                problems.append({"manifest": str(manifest_path), "path": rel, "problem": "sha256 mismatch",
                                 "expected": artifact.get("sha256"), "actual": digest})
    uncovered = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.name.endswith("manifest.json") and str(path.resolve()) not in covered:
            uncovered.append(str(path.relative_to(root)))
    return {"root": str(root), "manifests": len(manifests), "artifacts_checked": checked,
            "problems": problems, "uncovered_files": uncovered,
            "verdict": "PASS" if not problems else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--output")
    ns = ap.parse_args()
    report = verify(Path(ns.root))
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    if ns.output:
        Path(ns.output).write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("root", "manifests", "artifacts_checked", "verdict")}, ensure_ascii=False))
    if report["problems"]:
        print(json.dumps(report["problems"][:10], ensure_ascii=False, indent=1))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
