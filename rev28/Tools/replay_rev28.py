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
import subprocess
from typing import Any

FIXTURES = {
    "evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-frame.png": "d545043d3048e71231a502b413c1bc2a7d98db1a8a329d7d3a77916401bf64fc",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-preclick-ax.json": "668bed55234f1a275fba246eb7d5ec51e7d9cf7ab116872795166d8e5af60d56",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-menu-detect.json": "009c705f7767b0354064c3a3ec3e1261a6257b2a40f559b0338ab60d29158775",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-menu-frame-geometry.json": "8f236ebabf5a35ae573857dc0ce4f2476462285441ad954ad92f04b9c70453b1",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-v8-locate-save-all.json": "5f5ba237bb198d6f363a58cfa29141ca571429b78714c27b35a1a2b63c46a996",
    "evidence/20260921-rev27-save-all/attempt-07/s11e-final-gate.json": "fd44018d5b179383d577e0ab8b2195e6bf72de0b3468eb0f857b6d52a45f57cc",
    "evidence/20260916-route/attempt-07/v5-offline-replay.json": "5ad6aa01ca0eb5f52ab8812ebdcb03c3b27fd6a82904166f7d9cff115dd3b455",
    "evidence/20260916-route/attempt-07/v4-baseline-replay.json": "126b3c92be34f09e78287d356b2fce7d27437a0f61678f8fc32e5c6cc6684b03",
    "evidence/20260916-route/attempt-07/album-card-locate.json": "94694c921171f98c53b7fc79a350d0f7faf635c234ed17cf894b87f9fb0fd624",
    "evidence/20260916-route/attempt-07/album-open-verify.json": "aa0a2161d844b5cf7583514d2269c4db61f210c3cc85b57afa0f9d8b471a83ff",
    "evidence/20260916-route/attempt-07/screen-probe.json": "38130a6a540c099b3ca88e979a72684a467e158b4a78ce64bf4334ccdba6f77c",
    "evidence/20260916-route/attempt-12/frame-pre.png": "b88f7e097cc349853034494c6a7f970f1c524d3084dc4a4bed711dacab320c58",
    "evidence/20260916-route/attempt-12/album-card-locate-v6.json": "05bcea90f31587435a1c16b522938eeabc32b06788d4d85b002559eb5b036875",
    "evidence/20260916-route/attempt-12/live-window-geometry.json": "fdd68d750b3bb2d2b2fbf9c4ae6724cdfd30c69b94d3d1e07adba9d681092296",
    "evidence/20260916-route/attempt-12/s1-ax-pre.json": "fe5f3d685b7e2270c296b055923a8a3938925195453dae911e05368d42f0c0c3",
    "evidence/20260916-route/attempt-13/frame-menu-pre.png": "0118b12fb758aa86fdd5b181c56005a94eef1be4b7cd60b005b547d9a47f0fb6",
    "evidence/20260916-route/attempt-13/geometry-binding-preclick.json": "288dba46bc5a4e14350e991070c22851d3679d95ce38ca9dfd597ddce88f076a",
    "evidence/20260916-route/attempt-14/frame-pre.png": "7e16ddfff3a3a3c59ed19eda5fc08b0e6e7f7ac4bedb5a546c9cd4257d3a976d",
    "evidence/20260916-route/attempt-16/frame-s1.png": "d058139168683cda6546b0d52adb0e23dea3fc5d3aa4bd5e082c0c084f0ee6ab",
    "evidence/20260916-route/attempt-16/s1-window-ocr.json": "ddf202f0dbc6854159b6180d55c43bccc2299ac085689774ec46ec2a3739ae0a",
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
        require(digest == prefix, f"sha-mismatch:{rel}:{digest}", failures)
        manifest.append({"path": rel, "sha256": digest})

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

    ellipsis = load_json(root, "evidence/20260916-route/attempt-07/v5-offline-replay.json")
    require(ellipsis.get("verdict") == "ELIGIBLE", "attempt07:ellipsis-not-eligible", failures)
    require(ellipsis.get("ellipsis_dots") == [[304.5, 44.0], [304.5, 49.5], [304.5, 55.0]], "attempt07:ellipsis-structure", failures)
    require(ellipsis.get("click_point") == [304, 50], "attempt07:ellipsis-point", failures)

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

    replay = subprocess.run(
        [
            "swift", "run", "--quiet", "--package-path", str(root / "rev28"),
            "rev28replay", "--root", str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    production_replay: dict[str, Any] = {}
    if replay.returncode != 0:
        failures.append(f"production-locator-replay-failed:{replay.stderr.strip()}")
    else:
        try:
            production_replay = json.loads(replay.stdout)
        except json.JSONDecodeError as error:
            failures.append(f"production-locator-replay-invalid-json:{error}")
    require(production_replay.get("save_all_locator") == "candidate", "production:save-all-locator-disagreement", failures)
    require(production_replay.get("album_card_locator") == "candidate", "production:album-card-locator-disagreement", failures)

    report = {
        "schema": "rev28-historical-replay-v2",
        "fixture_count": len(manifest),
        "expected_fixture_count": len(FIXTURES),
        "manifest": sorted(manifest, key=lambda x: x["path"]),
        "checks": {
            "save_all_v8_reference_structure": rows,
            "save_all_v8_hard_check_count": len(hard),
            "attempt07_final_gate_all_pass": all(c.get("pass") is True for c in gate.get("checks", [])),
            "attempt07_ellipsis_verdict": ellipsis.get("verdict"),
            "attempt07_ellipsis_dots": ellipsis.get("ellipsis_dots"),
            "attempt12_album_card_verdict": card12.get("verdict"),
            "attempt12_count": str(card12.get("count_digits_read")),
            "attempt13_geometry_verdict": geometry13.get("verdict"),
            "attempt16_required_identities": [w for w in ["旻謙允禎成長日記", "2024/05/13~05/17", "57"] if w in words],
            "current_production_replay": production_replay,
        },
        "verdict": "PASS" if not failures and len(manifest) == len(FIXTURES) else "FAIL",
        "failures": sorted(failures),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
