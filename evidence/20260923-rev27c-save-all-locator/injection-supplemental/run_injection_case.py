#!/usr/bin/env python3
"""SUPPLEMENTAL offline negative test - historical-coordinate injection.

NOT part of the reviewed v8 selftest binding. The reviewed binding is
tools/v8/selftest/run_selftest.py (sha c94fc4074f0cd323ee53fe09428b0d38b61af04f5993ceb344acaa02e236f462,
43 cases) and its results.json
(sha 943f293995b8ecc3f51ad9fc672c1fe899ba37312dc377d14a809ee118affe6a).
This supplemental case exists so the attempt-05 negative matrix keeps a direct
decoy-injection fixture without perturbing those frozen bytes: case c19 was
authored pre-freeze, then withdrawn before freeze to restore the exact reviewed
byte state; its fixture is reused here from where it was left on disk.

What it proves (offline, zero GUI input, zero LINE interaction):

  * the frozen v8 locator (sha c5ad4686...) run on the attempt-05 menu frame
    with the decoy-injected geometry fixture (geo-a05-injected-history.json,
    sha 842cb933...) yields verdict ELIGIBLE with exactly one candidate;
  * that candidate is the same decision as the run over the clean geometry
    fixture (geo-a05.json): the injected historical fields (frozen-v5 ellipsis
    click point, historical v7 candidate, app-local fallback) have zero effect;
  * the candidate equals the current-frame-derived expectation and differs
    from every injected decoy value;
  * the injected run is deterministic (x2 byte-identical stdout), and the
    decoded JSON is identical to the clean-fixture run on the decision fields.

An offline ELIGIBLE verdict is NOT a live click authorization and this script
grants no authority. It has no GUI/network capability; its only write sites are
its own out/ directory and its own results.json.

Run with: /opt/homebrew/bin/python3 run_injection_case.py
"""
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "out")
RESULTS = os.path.join(HERE, "results.json")

TOOL = "evidence/20260916-route/tools/v8/locate_save_all_menu_item.py"
FRAME = "evidence/20260921-rev27-save-all/attempt-05/frame-menu-post1.png"
DET = "evidence/20260916-route/tools/v8/selftest/fixtures/det-a05.json"
GEO_CLEAN = "evidence/20260916-route/tools/v8/selftest/fixtures/geo-a05.json"
GEO_INJ = "evidence/20260916-route/tools/v8/selftest/fixtures/geo-a05-injected-history.json"

TOOL_SHA = "c5ad46861706a9a2c1c4d477caeda2a809c87c5488844f14a4d3efb34c668a86"
FRAME_SHA = "2f6bf83d8962e0eb129c5fe342e8c27fcc964add50c11a147a6bc4a0fa76c880"
INJ_SHA = "842cb93330e3183cf5c3cc7cd28e69b5714084499aa994f49cdc93d7fa2f3418"

EXPECT_FRAME_PX = [1297.333, 351.5]
EXPECT_SCREEN_PT = [648.667, 175.75]
EXPECT_APP_LOCAL = [319.667, 134.75]

DECOYS = {
    "historical_candidate_frame_px": [1313.5, 332.333],
    "historical_candidate_window_local_pt": [304.0, 50.0],
    "fallback_candidate_app_local_pt": [42.0, 988.0],
}
TOL = 0.002


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def close(seq, expected, tol=TOL):
    return len(seq) == len(expected) and all(
        abs(a - b) <= tol for a, b in zip(seq, expected))


def run_cli(geo, out_name):
    """Frozen v8 CLI, repo-relative args, same form as the reviewed selftest."""
    out_path = os.path.join(OUT, out_name)
    cmd = [sys.executable, "-B", TOOL, FRAME, "--detector-json", DET,
           "--geometry", geo, "--out", out_path]
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    raw = proc.stdout.decode("utf-8", errors="replace")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw)
    return proc.returncode, raw, out_path


def main():
    checks = []

    def check(name, ok, detail):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    tool_sha = sha256_file(os.path.join(ROOT, TOOL))
    frame_sha = sha256_file(os.path.join(ROOT, FRAME))
    inj_sha = sha256_file(os.path.join(ROOT, GEO_INJ))
    check("frozen_tool_binding", tool_sha == TOOL_SHA,
          {"expected": TOOL_SHA, "actual": tool_sha})
    check("frame_binding", frame_sha == FRAME_SHA,
          {"expected": FRAME_SHA, "actual": frame_sha})
    check("injected_fixture_binding", inj_sha == INJ_SHA,
          {"expected": INJ_SHA, "actual": inj_sha})

    with open(os.path.join(ROOT, GEO_INJ), encoding="utf-8") as f:
        injected = json.load(f)
    decoys_present = {k: injected.get(k) for k in DECOYS}
    check("decoy_fields_actually_present", decoys_present == DECOYS,
          decoys_present)

    rc_c, raw_c, path_c = run_cli(GEO_CLEAN, "clean-control.json")
    rc_1, raw_1, path_1 = run_cli(GEO_INJ, "injected-run-1.json")
    rc_2, raw_2, path_2 = run_cli(GEO_INJ, "injected-run-2.json")

    clean = json.loads(raw_c)
    inj1 = json.loads(raw_1)
    inj2 = json.loads(raw_2)

    cand1 = inj1.get("candidate") or {}
    candc = clean.get("candidate") or {}
    check("injected_verdict_eligible",
          inj1.get("verdict") == "ELIGIBLE" and rc_1 == 0,
          {"verdict": inj1.get("verdict"), "exit_code": rc_1})
    check("clean_control_verdict_eligible",
          clean.get("verdict") == "ELIGIBLE" and rc_c == 0,
          {"verdict": clean.get("verdict"), "exit_code": rc_c})
    check("injection_has_zero_effect_on_decision",
          inj1.get("verdict") == clean.get("verdict") and
          cand1.get("frame_px") == candc.get("frame_px") and
          cand1.get("screen_pt") == candc.get("screen_pt") and
          cand1.get("app_local_pt") == candc.get("app_local_pt"),
          {"injected_candidate": cand1, "clean_candidate": candc})
    check("candidate_equals_current_frame_derivation",
          close(cand1.get("frame_px", []), EXPECT_FRAME_PX) and
          close(cand1.get("screen_pt", []), EXPECT_SCREEN_PT) and
          close(cand1.get("app_local_pt", []), EXPECT_APP_LOCAL),
          {"frame_px": cand1.get("frame_px"),
           "screen_pt": cand1.get("screen_pt"),
           "app_local_pt": cand1.get("app_local_pt")})
    check("candidate_differs_from_every_decoy",
          all(not (close(cand1.get("frame_px", []), v) or
                   close(cand1.get("app_local_pt", []), v)) for v in DECOYS.values()),
          {"candidate": cand1,
           "decoys": DECOYS})
    check("injected_run_deterministic_x2",
          raw_1 == raw_2 and rc_1 == rc_2 and inj1 == inj2,
          {"run1_stdout_sha256": hashlib.sha256(raw_1.encode("utf-8")).hexdigest(),
           "run2_stdout_sha256": hashlib.sha256(raw_2.encode("utf-8")).hexdigest()})
    check("out_files_written",
          all(os.path.exists(p) for p in (path_c, path_1, path_2)),
          {"out_files": [os.path.relpath(p, ROOT) for p in (path_c, path_1, path_2)]})

    all_pass = all(c["pass"] for c in checks)
    results = {
        "schema": "rev27c-injection-supplemental/1",
        "artifact": ("evidence/20260923-rev27c-save-all-locator/"
                     "injection-supplemental/results.json"),
        "role": ("SUPPLEMENTAL negative test for the attempt-05 negative-matrix "
                 "item 'historical-coordinate injection'; not part of the reviewed "
                 "v8 selftest binding (run_selftest.py c94fc407..., results.json "
                 "943f2939..., 43 cases)"),
        "gui_input_count": 0,
        "authority": ("OFFLINE TEST ONLY - an ELIGIBLE verdict here is not a live "
                      "click authorization"),
        "tool": {"path": TOOL, "sha256": tool_sha},
        "inputs": {
            "frame": {"path": FRAME, "sha256": frame_sha},
            "detector_json": DET,
            "geometry_clean": GEO_CLEAN,
            "geometry_injected": {"path": GEO_INJ, "sha256": inj_sha},
        },
        "decoys_injected": DECOYS,
        "checks": checks,
        "summary": {"checks_total": len(checks),
                    "checks_passed": sum(1 for c in checks if c["pass"]),
                    "all_pass": all_pass},
        "run_outputs": {
            "clean_control": os.path.relpath(path_c, ROOT),
            "injected_run_1": os.path.relpath(path_1, ROOT),
            "injected_run_2": os.path.relpath(path_2, ROOT),
        },
    }
    payload = json.dumps(results, ensure_ascii=False, indent=1,
                         sort_keys=True) + "\n"
    with open(RESULTS, "w", encoding="utf-8") as f:
        f.write(payload)
    print("checks %d/%d pass; all_pass=%s"
          % (results["summary"]["checks_passed"],
             results["summary"]["checks_total"], all_pass))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
