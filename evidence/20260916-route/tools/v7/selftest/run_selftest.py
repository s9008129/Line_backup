#!/usr/bin/env python3
"""Deterministic selftest + offline replay for album_detail_lineage_guard (v7).

No GUI input, no network. Builds synthetic fixtures deterministically, runs the
guard as a subprocess on real attempt evidence and on synthetic negatives, and
writes results.json (+ per-case stdout) next to this file.

Replays (all offline, from existing evidence):
  attempt-12 pre-click list   -> must REFUSE
  attempt-12 post-click       -> strict AX-diff-form evidence: REFUSE (insufficient
                                 AX form); bridged same-surface set: VERIFIED
  attempt-13 detail           -> VERIFIED
  attempt-03 (frozen ALBUM_OPEN_VERIFIED present) -> must REFUSE; composite must
                                 never PASS
"""
import copy
import hashlib
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
V7 = os.path.dirname(HERE)
TOOLS = os.path.dirname(V7)
ROUTE = os.path.dirname(TOOLS)
EVID = os.path.dirname(ROUTE)
ROOT = os.path.dirname(EVID)
GUARD = os.path.join(V7, "album_detail_lineage_guard.py")
READER_DIR = os.path.join(TOOLS, "v5")
A12 = os.path.join(ROOT, "evidence", "20260916-route", "attempt-12")
A13 = os.path.join(ROOT, "evidence", "20260916-route", "attempt-13")
A03 = os.path.join(ROOT, "evidence", "20260921-rev27-save-all", "attempt-03")
GEN = os.path.join(HERE, "generated")
OUT = os.path.join(HERE, "out")
os.makedirs(GEN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)


def jload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def jdump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


a13_inventory = jload(os.path.join(A13, "s1-ax-pre.json"))
a03_inventory = jload(os.path.join(A03, "s1-ax-pre.json"))

FIXTURES = {}


def build_fixtures():
    # two main windows
    inv = copy.deepcopy(a13_inventory)
    inv["windows"][1]["main"] = True
    p = os.path.join(GEN, "inventory-two-main-windows.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # two ax-focused windows
    inv = copy.deepcopy(a13_inventory)
    inv["windows"][1]["is_ax_focused_window"] = True
    p = os.path.join(GEN, "inventory-two-focused-windows.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # wrong LINE window: the big main window is focused+main (kept inside the
    # display so the refusal comes from the AX surface class, not the bounds)
    inv = copy.deepcopy(a13_inventory)
    for w in inv["windows"]:
        big = w["size_points"] == [1147, 699]
        if big:
            w["position_points"] = [0, 37]
        w["main"] = bool(big)
        w["is_ax_focused_window"] = bool(big)
        w["focused"] = bool(big)
    p = os.path.join(GEN, "inventory-wrong-line-window.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # the detail window EXISTS but the group/list window is focused+main:
    # the guard must verify only the focused window and therefore refuse
    inv = copy.deepcopy(a13_inventory)
    for w in inv["windows"]:
        group = w["position_points"] == [0, 30]
        w["main"] = bool(group)
        w["is_ax_focused_window"] = bool(group)
        w["focused"] = bool(group)
    p = os.path.join(GEN, "inventory-a13-group-focused-detail-unfocused.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # historical coordinate injection: a03 list state, group window hard-set to [337,30]
    inv = copy.deepcopy(a03_inventory)
    inv["windows"][0]["position_points"] = [337, 30]
    p = os.path.join(GEN, "inventory-a03-historical-coordinate-injection.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # malformed: truncated JSON
    raw = open(os.path.join(A13, "s1-ax-pre.json"), "r", encoding="utf-8").read()
    p = os.path.join(GEN, "inventory-truncated.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write(raw[:200])
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # malformed: display block removed
    inv = copy.deepcopy(a13_inventory)
    del inv["display"]
    p = os.path.join(GEN, "inventory-missing-display.json")
    jdump(p, inv)
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # synthetic album-list AX state (wrong-window case)
    p = os.path.join(GEN, "state-synthetic-list.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write('Window: "", App: LINE.\n'
                '0 標準視窗 Secondary Actions: Raise\n'
                '\t1 文字欄位 (settable) Secondary Actions: Raise\n'
                '\t2 列表 (showing 0-100 of 101 items)\n'
                '\t\t3 row\n\t\t4 row\n\t\t5 row\n'
                '\t6 捲軸 (settable) 1077\n'
                '\t7 關閉按鈕\n\t8 縮到最小按鈕\n'
                'The focused UI element is 1 文字欄位 (settable)\n')
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # empty AX state
    p = os.path.join(GEN, "state-empty.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("")
    FIXTURES[os.path.basename(p)] = sha256_file(p)

    # occluded frame: attempt-13 frame with the bottom 55% of the detail-window
    # rect painted over (deterministic solid fill) -> binding must fail
    frame = Image.open(os.path.join(A13, "frame-pre.png")).convert("RGB")
    draw = ImageDraw.Draw(frame)
    x0, y0, x1, y1 = 674, 60, 1328, 1346
    oy = int(y0 + (y1 - y0) * 0.45)
    for yy in range(oy, y1):
        draw.line([(x0, yy), (x1 - 1, yy)], fill=(40, 40, 40))
    p = os.path.join(GEN, "frame-occluded-detail-bottom.png")
    frame.save(p)
    FIXTURES[os.path.basename(p)] = sha256_file(p)


CASES = []


def case(name, description, args, expect_exit, expect_reason_prefixes=(),
         expect_verified=False, expect_composite=None):
    CASES.append({
        "name": name, "description": description, "args": args,
        "expect_exit": expect_exit,
        "expect_reason_prefixes": list(expect_reason_prefixes),
        "expect_verified": expect_verified, "expect_composite": expect_composite})


def guard_args(inventory, state, shot, frame,
               expected=("2024/05/13", "05/17", "57"), frozen=None):
    args = ["--window-inventory", inventory, "--window-ax-state", state,
            "--window-screenshot", shot, "--frame", frame,
            "--expect-start", expected[0], "--expect-end", expected[1],
            "--expect-count", expected[2],
            "--reader-dir", READER_DIR]
    if frozen:
        args += ["--frozen-album-open-json", frozen]
    return args


A13_INV = os.path.join(A13, "s1-ax-pre.json")
A13_STATE = os.path.join(A13, "cua-ax-state-s1.txt")
A13_SHOT = os.path.join(A13, "cua-window-s1.jpg")
A13_FRAME = os.path.join(A13, "frame-pre.png")
A12_INV = os.path.join(A12, "s1-ax-pre.json")
A12_STATE_S1 = os.path.join(A12, "cua-ax-state-s1.txt")
A12_STATE_S5 = os.path.join(A12, "cua-ax-state-s5.txt")
A12_SHOT_LIST = os.path.join(A12, "cua-window-s1.jpg")
A12_SHOT_DETAIL = os.path.join(A12, "cua-window-s5.jpg")
A12_FRAME_PRE = os.path.join(A12, "frame-pre.png")
A12_FRAME_POST = os.path.join(A12, "frame-post.png")
A12_FROZEN = os.path.join(A12, "album-open-verify.json")
A03_INV = os.path.join(A03, "s1-ax-pre.json")
A03_STATE = os.path.join(A03, "cua-ax-state-s1.txt")
A03_SHOT = os.path.join(A03, "cua-window-s1.jpg")
A03_FRAME = os.path.join(A03, "frame-s1.png")
A03_FROZEN_WINDOW = os.path.join(A03, "s3-album-open-verify-window.json")


def build_cases():
    case("pos-attempt-13-detail-strict",
         "attempt-13 detail surface, same-round inventory+state+shot+frame",
         guard_args(A13_INV, A13_STATE, A13_SHOT, A13_FRAME), 0, expect_verified=True,
         expect_composite="NOT_EVALUATED")
    case("pos-attempt-12-post-bridged",
         "attempt-12 post-click surface via the byte-identical window screenshot "
         "bridge (a13 s1 inventory/state; a12 frame-post binds at MAD 2.259)",
         guard_args(A13_INV, A13_STATE, A12_SHOT_DETAIL, A12_FRAME_POST), 0,
         expect_verified=True)
    case("pos-attempt-12-composite-bridged",
         "as above + frozen attempt-12 album-open verdict bound to the same frame",
         guard_args(A13_INV, A13_STATE, A12_SHOT_DETAIL, A12_FRAME_POST,
                    frozen=A12_FROZEN), 0,
         expect_verified=True, expect_composite="ALBUM_OPEN_VERIFIED_COMPOSITE_PASS")
    case("neg-attempt-12-pre-strict",
         "attempt-12 pre-click must refuse; its saved S1 CU state text is the "
         "no-change form, so the refusal is the AX-form check (full-tree list "
         "refusals are covered by the attempt-03 cases)",
         guard_args(A12_INV, A12_STATE_S1, A12_SHOT_LIST, A12_FRAME_PRE), 2,
         expect_reason_prefixes=("SURFACE_AX_NOT_FULL_TREE",))
    case("neg-detail-exists-but-group-focused",
         "a detail window exists but the group/list window is the focused/main "
         "window -> the guard must refuse (never verify off an unfocused window)",
         guard_args(os.path.join(GEN, "inventory-a13-group-focused-detail-unfocused.json"),
                    A03_STATE, A03_SHOT, A03_FRAME), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-attempt-12-post-strict-ax-diff-form",
         "attempt-12 post-click with its actual CU diff-form state text: the guard "
         "requires a full-tree AX read in the same round -> refuse",
         guard_args(A12_INV, A12_STATE_S5, A12_SHOT_DETAIL, A12_FRAME_POST), 2,
         expect_reason_prefixes=("SURFACE_AX_NOT_FULL_TREE",))
    case("neg-attempt-03-regression-frozen-verdict",
         "attempt-03 list surface WITH its frozen ALBUM_OPEN_VERIFIED artifact: "
         "guard refuses, composite must never pass",
         guard_args(A03_INV, A03_STATE, A03_SHOT, A03_FRAME,
                    frozen=A03_FROZEN_WINDOW), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-attempt-03-count57-no-detail",
         "count 57 visible but no detail surface (attempt-03 strict)",
         guard_args(A03_INV, A03_STATE, A03_SHOT, A03_FRAME), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-detail-title-but-list-controls-active",
         "detail window pixels but the focused window's AX tree is the list tree "
         "(list controls still active) -> refuse",
         guard_args(A13_INV, A03_STATE, A13_SHOT, A13_FRAME), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-wrong-line-window",
         "the big LINE window is the focused/main window; its AX state is a list "
         "surface -> refuse",
         guard_args(os.path.join(GEN, "inventory-wrong-line-window.json"),
                    os.path.join(GEN, "state-synthetic-list.txt"),
                    A13_SHOT, A13_FRAME), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-multiple-focused-windows",
         "two ax-focused windows -> ambiguous -> refuse",
         guard_args(os.path.join(GEN, "inventory-two-focused-windows.json"),
                    A13_STATE, A13_SHOT, A13_FRAME), 2,
         expect_reason_prefixes=("TARGET_AMBIGUOUS",))
    case("neg-two-main-windows",
         "two main windows -> ambiguous -> refuse",
         guard_args(os.path.join(GEN, "inventory-two-main-windows.json"),
                    A13_STATE, A13_SHOT, A13_FRAME), 2,
         expect_reason_prefixes=("TARGET_AMBIGUOUS",))
    case("neg-missing-ax-tree-diff-form",
         "CU 'no change' diff form is not a full tree -> refuse",
         guard_args(A13_INV, os.path.join(A13, "cua-ax-state-s6.txt"),
                    A13_SHOT, A13_FRAME), 2,
         expect_reason_prefixes=("SURFACE_AX_NOT_FULL_TREE",))
    case("neg-empty-ax-tree",
         "empty AX state text -> refuse",
         guard_args(A13_INV, os.path.join(GEN, "state-empty.txt"), A13_SHOT, A13_FRAME),
         2, expect_reason_prefixes=("SURFACE_AX_NOT_FULL_TREE",))
    case("neg-stale-frame-binding",
         "attempt-13 detail screenshot against attempt-03's frame -> binding fails",
         guard_args(A13_INV, A13_STATE, A13_SHOT, A03_FRAME), 2,
         expect_reason_prefixes=("BINDING_FAILED",))
    case("neg-occluded-detail",
         "attempt-13 frame with the detail-window region partly painted over -> "
         "binding fails",
         guard_args(A13_INV, A13_STATE, A13_SHOT,
                    os.path.join(GEN, "frame-occluded-detail-bottom.png")), 2,
         expect_reason_prefixes=("BINDING_FAILED",))
    case("neg-malformed-evidence-truncated",
         "truncated inventory JSON -> refuse at evidence stage",
         guard_args(os.path.join(GEN, "inventory-truncated.json"), A13_STATE,
                    A13_SHOT, A13_FRAME), 6,
         expect_reason_prefixes=("EVIDENCE_",))
    case("neg-malformed-evidence-missing-display",
         "inventory without display block -> refuse",
         guard_args(os.path.join(GEN, "inventory-missing-display.json"), A13_STATE,
                    A13_SHOT, A13_FRAME), 6,
         expect_reason_prefixes=("EVIDENCE_",))
    case("neg-historical-coordinate-injection",
         "a03 list state with the group window's rect injected as the historical "
         "[337,30] -> coordinates alone never verify -> refuse",
         guard_args(os.path.join(GEN, "inventory-a03-historical-coordinate-injection.json"),
                    A03_STATE, A03_SHOT, A03_FRAME), 2,
         expect_reason_prefixes=("SURFACE_HAS_LIST_CONTROLS",))
    case("neg-wrong-album-title",
         "detail surface but a different expected album title -> refuse",
         guard_args(A13_INV, A13_STATE, A13_SHOT, A13_FRAME,
                    expected=("2024/06/01", "06/05", "57")), 2,
         expect_reason_prefixes=("HEADER_TITLE_NOT_FOUND",))
    case("neg-count-mismatch-in-header",
         "detail header says 57 photos but the round expects 58 -> refuse",
         guard_args(A13_INV, A13_STATE, A13_SHOT, A13_FRAME,
                    expected=("2024/05/13", "05/17", "58")), 2,
         expect_reason_prefixes=("PHOTO_COUNT_CONTEXT_MISSING_OR_MISMATCH",))
    case("neg-frozen-artifact-not-bound",
         "lineage verified but the frozen artifact's post frame is another round's "
         "capture -> composite FAIL",
         guard_args(A13_INV, A13_STATE, A13_SHOT, A13_FRAME,
                    frozen=A03_FROZEN_WINDOW), 3,
         expect_verified=True,
         expect_composite="ALBUM_OPEN_VERIFIED_COMPOSITE_FAIL")


def run_case(c):
    cmd = [sys.executable, GUARD] + c["args"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = None
    try:
        out = json.loads(proc.stdout)
    except Exception:
        pass
    with open(os.path.join(OUT, c["name"] + ".json"), "w", encoding="utf-8") as f:
        f.write(proc.stdout)
    reasons = (out or {}).get("refusal_reasons", []) or []
    verdict_ok = (out is not None) and (proc.returncode == c["expect_exit"])
    if c["expect_verified"]:
        verdict_ok = verdict_ok and out.get("verdict") == "ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED"
    else:
        verdict_ok = verdict_ok and out.get("verdict") == "REFUSED"
    reasons_ok = all(any(r.startswith(p) for r in reasons)
                     for p in c["expect_reason_prefixes"])
    composite = (out or {}).get("composite", {}).get("verdict")
    composite_ok = True if c["expect_composite"] is None else composite == c["expect_composite"]
    entry = {
        "name": c["name"], "description": c["description"],
        "expected": {"exit_code": c["expect_exit"], "verified": c["expect_verified"],
                     "reason_prefixes": c["expect_reason_prefixes"],
                     "composite": c["expect_composite"]},
        "actual": {"exit_code": proc.returncode, "verdict": (out or {}).get("verdict"),
                   "refusal_reasons": reasons, "composite": composite},
        "pass": bool(verdict_ok and reasons_ok and composite_ok)}
    return entry


def main():
    build_fixtures()
    build_cases()
    entries = [run_case(c) for c in CASES]

    # determinism: the same case twice must produce byte-identical stdout
    first = open(os.path.join(OUT, "pos-attempt-13-detail-strict.json"),
                 "r", encoding="utf-8").read()
    run_case({"name": "determinism-repeat", "description": "repeat run",
              "args": CASES[0]["args"], "expect_exit": 0, "expect_verified": True,
              "expect_reason_prefixes": [], "expect_composite": "NOT_EVALUATED"})
    second = open(os.path.join(OUT, "determinism-repeat.json"),
                  "r", encoding="utf-8").read()
    deterministic = first == second

    # attempt-03 sweep: no attempt-03-derived input set may ever verify
    sweep = []
    combos = [
        (A03_INV, A03_STATE, A03_SHOT, A03_FRAME),
        (A03_INV, A03_STATE, A13_SHOT, A03_FRAME),
        (A13_INV, A13_STATE, A13_SHOT, A03_FRAME),
        (A13_INV, A03_STATE, A03_SHOT, A13_FRAME),
        (os.path.join(GEN, "inventory-a03-historical-coordinate-injection.json"),
         A03_STATE, A03_SHOT, A03_FRAME),
    ]
    for i, (inv, st, sh, fr) in enumerate(combos):
        proc = subprocess.run([sys.executable, GUARD] + guard_args(inv, st, sh, fr),
                              capture_output=True, text=True)
        out = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}
        sweep.append({"combo": i, "exit_code": proc.returncode,
                      "verdict": out.get("verdict"),
                      "verified": out.get("verdict") == "ALBUM_DETAIL_WINDOW_LINEAGE_VERIFIED"})
    sweep_ok = all(not s["verified"] for s in sweep)

    result = {
        "artifact": "album_detail_lineage_guard v7 selftest + offline replay results",
        "guard": {"path": os.path.relpath(GUARD, ROOT), "sha256": sha256_file(GUARD)},
        "fixtures": FIXTURES,
        "cases": entries,
        "determinism": {"repeat_byte_identical": deterministic},
        "attempt_03_sweep": {"combos": sweep, "no_combo_verified": sweep_ok},
        "totals": {
            "cases": len(entries),
            "passed": sum(1 for e in entries if e["pass"]),
            "failed": [e["name"] for e in entries if not e["pass"]],
        },
        "verdict": "SELFTEST_PASS" if (all(e["pass"] for e in entries) and deterministic
                                       and sweep_ok) else "SELFTEST_FAIL",
    }
    payload = json.dumps(result, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        f.write(payload + "\n")
    print(payload)
    return 0 if result["verdict"] == "SELFTEST_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
