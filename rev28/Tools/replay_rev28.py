#!/usr/bin/env python3
"""Rev28 W3 historical replay.

Offline only. Binds the 20 reviewed fixtures by SHA-256 prefix and checks
semantic invariants already captured in their append-only JSON evidence.
Produces deterministic JSON (no wall clock, no absolute workspace paths).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

FIXTURES = {
    "evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-frame.png": "d545043d",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-ax.json": "668bed55",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-menu-detect.json": "009c705f",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-menu-frame-geometry.json": "8f236eba",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-v8-locate-save-all.json": "5f5ba237",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-final-gate.json": "fd44018d",
    "evidence/20260916-route/attempt-07/v5-offline-replay.json": "5ad6aa01",
    "evidence/20260916-route/attempt-07/v4-baseline-replay.json": "126b3c92",
    "evidence/20260916-route/attempt-07/album-card-locate.json": "94694c92",
    "evidence/20260916-route/attempt-07/album-open-verify.json": "aa0a2161",
    "evidence/20260916-route/attempt-07/screen-probe.json": "38130a6a",
    "evidence/20260916-route/attempt-12/frame-pre.png": "b88f7e09",
    "evidence/20260916-route/attempt-12/album-card-locate-v6.json": "05bcea90",
    "evidence/20260916-route/attempt-12/live-window-geometry.json": "fdd68d75",
    "evidence/20260916-route/attempt-12/s1-ax-pre.json": "fe5f3d68",
    "evidence/20260916-route/attempt-13/frame-menu-pre.png": "0118b12f",
    "evidence/20260916-route/attempt-13/geometry-binding-preclick.json": "288dba46",
    "evidence/20260916-route/attempt-14/frame-pre.png": "7e16ddff",
    "evidence/20260916-route/attempt-16/frame-s1.png": "d0581391",
    "evidence/20260916-route/attempt-16/s1-window-ocr.json": "ddf202f0",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(root: Path, rel: str) -> Any:
    with (root / rel).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(condition: bool, name: str, failures: list[str]) -> None:
    if not condition:
        failures.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    manifest = []
    failures: list[str] = []
    for rel, prefix in FIXTURES.items():
        path = root / rel
        if not path.is_file():
            failures.append(f"missing:{rel}")
            continue
        digest = sha256(path)
        require(digest.startswith(prefix), f"sha-mismatch:{rel}:{digest}", failures)
        manifest.append({"path": rel, "sha256": digest, "reviewed_prefix": prefix})

    # Save-All menu replay: exact target, full five-row reference structure,
    # safe candidate and every historical HARD check passed.
    v8 = load_json(root, "evidence/20260921-rev27-save-all/attempt-07/s11e-v8-locate-save-all.json")
    require(v8.get("verdict") == "ELIGIBLE", "v8:not-eligible", failures)
    rows = [row.get("cjk_text") for row in v8.get("rows", [])]
    require(rows == ["選擇項目", "修改相簿名稱", "儲存全部", "刪除相簿", "分享相簿"], "v8:reference-rows", failures)
    require(v8.get("target", {}).get("cjk_text") == "儲存全部", "v8:target", failures)
    hard = [c for c in v8.get("checks", []) if c.get("class") == "HARD"]
    require(bool(hard) and all(c.get("pass") is True for c in hard), "v8:hard-check", failures)
    candidate = v8.get("candidate", {}).get("frame_px", [])
    x_safe = v8.get("candidate_derivation", {}).get("x_safe_frame_px", [])
    y_safe = v8.get("candidate_derivation", {}).get("y_safe_frame_px", [])
    require(
        len(candidate) == 2 and len(x_safe) == 2 and len(y_safe) == 2
        and x_safe[0] <= candidate[0] <= x_safe[1]
        and y_safe[0] <= candidate[1] <= y_safe[1],
        "v8:candidate-outside-safe-region",
        failures,
    )

    gate = load_json(root, "evidence/20260921-rev27-save-all/attempt-07/s11e-final-gate.json")
    require(all(c.get("pass") is True for c in gate.get("checks", [])), "attempt07:final-gate", failures)

    card12 = load_json(root, "evidence/20260916-route/attempt-12/album-card-locate-v6.json")
    require(card12.get("verdict") == "ELIGIBLE", "attempt12:album-card", failures)
    require(str(card12.get("count_digits_read")) == "57", "attempt12:count", failures)
    require(card12.get("dispatch", {}).get("dispatched") is False, "attempt12:historical-dispatch", failures)

    geometry13 = load_json(root, "evidence/20260916-route/attempt-13/geometry-binding-preclick.json")
    require(geometry13.get("verdict") == "GEOMETRY_BINDING_PASS", "attempt13:geometry-binding", failures)

    ocr16 = load_json(root, "evidence/20260916-route/attempt-16/s1-window-ocr.json")
    words = ocr16.get("words", [])
    for expected in ["旻謙允禎成長日記", "2024/05/13~05/17", "57"]:
        require(expected in words, f"attempt16:missing-identity:{expected}", failures)
    require("旻謙允楨成長日記" not in words, "attempt16:zhen-glyph-confusion", failures)

    report = {
        "schema": "rev28-historical-replay-v1",
        "fixture_count": len(manifest),
        "expected_fixture_count": len(FIXTURES),
        "manifest": sorted(manifest, key=lambda x: x["path"]),
        "checks": {
            "save_all_v8_reference_structure": rows,
            "save_all_v8_hard_check_count": len(hard),
            "attempt07_final_gate_all_pass": all(c.get("pass") is True for c in gate.get("checks", [])),
            "attempt12_album_card_verdict": card12.get("verdict"),
            "attempt12_count": str(card12.get("count_digits_read")),
            "attempt13_geometry_verdict": geometry13.get("verdict"),
            "attempt16_required_identities": [w for w in ["旻謙允禎成長日記", "2024/05/13~05/17", "57"] if w in words],
        },
        "verdict": "PASS" if not failures and len(manifest) == len(FIXTURES) else "FAIL",
        "failures": sorted(failures),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
