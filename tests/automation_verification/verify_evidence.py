#!/usr/bin/env python3
"""Independent read-back verifier for an evidence tree.

Re-reads every manifest found under the given root — tree manifests (`manifest.json`,
`*.manifest.json`) and manifest supplements (`manifest-*.json`, e.g. `manifest-supplement.json`
which carries SHA-256+bytes for verifier-owned `manifest.json` chains) — recomputes SHA-256 and
byte length for each listed artifact, and reports mismatches, missing files and uncovered files.

Read-only: never writes into the evidence tree. Its own report file
(`readback-verification.json`, or `--ignore` names) is a derived document and is therefore not
required to be covered by a manifest.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import sha256_bytes

DEFAULT_IGNORE = ("readback-verification.json",)


def _is_manifest_name(name: str) -> bool:
    return name.endswith("manifest.json") or (name.startswith("manifest-") and name.endswith(".json"))


def _manifest_targets(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and _is_manifest_name(path.name):
            yield path


def verify(root: Path, *, ignore=DEFAULT_IGNORE) -> dict:
    manifests = list(_manifest_targets(root))
    problems = []
    covered = set()
    checked = 0
    supplements = 0
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append({"manifest": str(manifest_path), "problem": f"unreadable manifest: {exc}"})
            continue
        base = manifest_path.parent
        entries = manifest.get("artifacts")
        if entries is None:
            entries = manifest.get("files")
            supplements += 1
        if entries is None:
            problems.append({"manifest": str(manifest_path), "problem": "manifest has no artifacts/files list"})
            continue
        for artifact in entries:
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
    ignored = set(ignore) | {m.name for m in manifests}
    uncovered = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in ignored and str(path.resolve()) not in covered:
            uncovered.append(str(path.relative_to(root)))
    return {"root": str(root), "manifests": len(manifests), "supplements": supplements,
            "artifacts_checked": checked, "ignored_names": sorted(ignored),
            "problems": problems, "uncovered_files": uncovered,
            "verdict": "PASS" if not problems and not uncovered else "FAIL"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--output")
    ap.add_argument("--ignore", action="append", default=[])
    ns = ap.parse_args()
    report = verify(Path(ns.root), ignore=tuple(DEFAULT_IGNORE) + tuple(ns.ignore))
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    if ns.output:
        Path(ns.output).write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("root", "manifests", "supplements", "artifacts_checked", "verdict")},
                     ensure_ascii=False))
    if report["problems"]:
        print(json.dumps(report["problems"][:10], ensure_ascii=False, indent=1))
    if report["uncovered_files"]:
        print(json.dumps({"uncovered_files": report["uncovered_files"][:10]}, ensure_ascii=False, indent=1))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
