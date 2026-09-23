#!/usr/bin/env python3
"""Rev27c offline replay: run the frozen v8 locator on historical menu frames.

Zero GUI input. Reads only existing evidence; writes only under this replay
directory (inputs/, out/, replay-record.json). The replay inputs for attempt-13
and attempt-19 are frame-SHA re-bindings of those rounds' OWN AX window
geometry records (provenance recorded per input); they confer no live
authority. An offline ELIGIBLE verdict never authorizes a click.
"""
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
EVID = os.path.dirname(ROUND)
ROOT = os.path.dirname(EVID)
TOOL = os.path.join(ROOT, "evidence", "20260916-route", "tools", "v8",
                    "locate_save_all_menu_item.py")
A05 = os.path.join(ROOT, "evidence", "20260921-rev27-save-all", "attempt-05")
A13 = os.path.join(ROOT, "evidence", "20260916-route", "attempt-13")
A19 = os.path.join(ROOT, "evidence", "20260916-route", "attempt-19")
INPUTS = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
os.makedirs(INPUTS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "evidence", "20260916-route", "tools", "v8"))
from PIL import Image  # noqa: E402


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jdump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def write_geometry(fname, frame_sha, pos, size, provenance):
    path = os.path.join(INPUTS, fname)
    jdump(path, {
        "artifact": fname + " (Rev27c offline replay input)",
        "frame_sha256": frame_sha,
        "capture_scale": 2,
        "window_index": 0,
        "window_position_points": pos,
        "window_size_points": size,
        "window_point_rect": [pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]],
        "provenance": provenance,
        "authority": ("OFFLINE REPLAY INPUT ONLY - confers no live authority; a "
                      "future live round must produce its own fresh AX read bound "
                      "to its own fresh frame"),
    })
    return path


def run_live(tag, cwd, frame_arg, detector_arg, geometry_arg, out_name):
    out_path = os.path.join(OUT, out_name)
    cmd = [sys.executable, "-B", TOOL, frame_arg,
           "--detector-json", detector_arg, "--geometry", geometry_arg,
           "--out", out_path]
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    raw = proc.stdout.decode("utf-8", errors="replace")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw)
    parsed = json.loads(raw)
    return {"name": out_name, "exit_code": proc.returncode,
            "stdout_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "verdict": parsed.get("verdict"), "reason": parsed.get("reason"),
            "candidate": parsed.get("candidate"),
            "target": parsed.get("target"),
            "row_tiers": [m.get("tier") for m in
                          parsed.get("checks", [{}])[2].get("detail", {}).get("matches", [])
                          ] if len(parsed.get("checks", [])) > 2 else None,
            "checks": [{"name": c["name"], "pass": c["pass"]}
                       for c in parsed.get("checks", [])]}


def main():
    record = {
        "artifact": "Rev27c offline replay record (zero GUI input)",
        "tool": {"path": os.path.relpath(TOOL, ROOT), "sha256": sha256_file(TOOL)},
        "inputs_authority": ("replay-only frame-SHA re-bindings of the rounds' own "
                             "AX geometry evidence; no live authority"),
        "runs": {},
        "notes": [],
    }

    # --- attempt-13: replay geometry derived from attempt-13's own AX record ---
    a13_frame = os.path.join(A13, "frame-menu-post1.png")
    a13_frame_rel = "evidence/20260916-route/attempt-13/frame-menu-post1.png"
    a13_geo_src = os.path.join(A13, "live-window-geometry.json")
    a13_bind_src = os.path.join(A13, "geometry-binding-preclick.json")
    a13_geometry = write_geometry(
        "attempt-13-menu-frame-geometry.json", sha256_file(a13_frame),
        [337, 30], [327, 643],
        ("window rect [337,30] 327x643 from %s (sha256 %s; AX read of the focused+main "
         "album-detail window, pre/post identical in the same uninterrupted session as the "
         "menu frames) and %s (sha256 %s; binds the same rect to this session's "
         "frame-menu-pre.png at MAD 2.255). Re-bound to the menu frame sha for this "
         "offline replay only." % (
             os.path.relpath(a13_geo_src, ROOT), sha256_file(a13_geo_src),
             os.path.relpath(a13_bind_src, ROOT), sha256_file(a13_bind_src))))
    a13_detector = os.path.join(A13, "s6-menu-pairB1.json")
    for i in (1, 2):
        record["runs"]["attempt-13-replay-%d" % i] = run_live(
            "attempt-13", ROOT, a13_frame_rel,
            os.path.relpath(a13_detector, ROOT), a13_geometry,
            "attempt-13-replay-%d.json" % i)
    record["runs"]["attempt-13-replay-1"]["inputs"] = {
        "frame": a13_frame_rel, "frame_sha256": sha256_file(a13_frame),
        "detector_json": os.path.relpath(a13_detector, ROOT),
        "detector_sha256": sha256_file(a13_detector),
        "geometry_json": os.path.relpath(a13_geometry, ROOT),
        "geometry_sha256": sha256_file(a13_geometry)}

    # --- attempt-19: replay geometry derived from attempt-19's own AX record ---
    a19_frame = os.path.join(A19, "frame-menu-post1.png")
    a19_geo_src = os.path.join(A19, "live-window-geometry.json")
    a19_bind_src = os.path.join(A19, "a5-frame-window-binding.json")
    a19_geometry = write_geometry(
        "attempt-19-menu-frame-geometry.json", sha256_file(a19_frame),
        [337, 49], [327, 643],
        ("window rect [337,49] 327x643 from %s (ax_window position [337,49], size "
         "[327,643]; verdict GEOMETRY_BINDING_PASS, MAD 2.228, bound there to this "
         "round's frame-post.png) and scale 2 from %s; corroborated offline in "
         "replay-record.json by a window-region MAD check between frame-post.png and "
         "frame-menu-post1.png over the region left of the popup overlay. Re-bound to "
         "the menu frame sha for this offline replay only." % (
             os.path.relpath(a19_bind_src, ROOT), os.path.relpath(a19_geo_src, ROOT))))
    a19_detector = os.path.join(A19, "s6-menu-pairB1.json")
    for i in (1, 2):
        record["runs"]["attempt-19-replay-%d" % i] = run_live(
            "attempt-19", A19, "frame-menu-post1.png", "s6-menu-pairB1.json",
            a19_geometry, "attempt-19-replay-%d.json" % i)
    record["runs"]["attempt-19-replay-1"]["inputs"] = {
        "frame": "frame-menu-post1.png", "frame_sha256": sha256_file(a19_frame),
        "detector_json": "s6-menu-pairB1.json",
        "detector_sha256": sha256_file(a19_detector),
        "geometry_json": os.path.relpath(a19_geometry, ROOT),
        "geometry_sha256": sha256_file(a19_geometry)}

    # offline corroboration: attempt-19 menu frame still binds the [337,49] window
    # over the region left of the popup overlay (menu bbox x0 = 1245 px)
    post = Image.open(os.path.join(A19, "frame-post.png")).convert("L")
    menu = Image.open(a19_frame).convert("L")
    region = (674, 98, 1245, 1384)
    a = post.crop(region)
    b = menu.crop(region)
    pa, pb = a.tobytes(), b.tobytes()
    mad = sum(abs(x - y) for x, y in zip(pa, pb)) / float(len(pa))
    record["attempt-19-window-binding-corrob"] = {
        "method": ("gray MAD between frame-post.png and frame-menu-post1.png over the "
                   "window rect region left of the popup overlay (menu bbox x0=1245), "
                   "both cropped at the SAME frame coordinates from the [337,49] window "
                   "rect"),
        "region_px": list(region), "mad_mean": round(mad, 3),
        "rule": "MAD <= 12.0 supports that the window rect of the bound frame-post.png "
                "still describes the menu frame's window position",
        "pass": mad <= 12.0,
    }

    # --- attempt-05: live-round inputs, replayed twice ---
    a05_frame_rel = "frame-menu-post1.png"
    for i in (1, 2):
        record["runs"]["attempt-05-replay-%d" % i] = run_live(
            "attempt-05", A05, a05_frame_rel, "s6-menu-pairB1.json",
            "live-window-geometry-post1.json", "attempt-05-replay-%d.json" % i)
    record["runs"]["attempt-05-replay-1"]["inputs"] = {
        "frame": a05_frame_rel,
        "frame_sha256": sha256_file(os.path.join(A05, "frame-menu-post1.png")),
        "detector_json": "s6-menu-pairB1.json (attempt-05's own run)",
        "detector_sha256": sha256_file(os.path.join(A05, "s6-menu-pairB1.json")),
        "geometry_json": "live-window-geometry-post1.json (attempt-05's own AX read, "
                         "frame-bound)",
        "geometry_sha256": sha256_file(
            os.path.join(A05, "live-window-geometry-post1.json"))}

    # determinism: byte comparison of the two runs per frame
    det = {}
    for tag in ("attempt-05", "attempt-13", "attempt-19"):
        a = record["runs"][tag + "-replay-1"]["stdout_sha256"]
        b = record["runs"][tag + "-replay-2"]["stdout_sha256"]
        det[tag] = {"run1_sha256": a, "run2_sha256": b,
                    "byte_identical": a == b}
    record["determinism"] = det

    # historical-candidate consistency
    r13 = record["runs"]["attempt-13-replay-1"]
    hist13 = {"source": ("evidence/20260921-rev27-save-all/attempt-02/selftest/"
                         "result-positive1.json (frozen v7-class locator, ELIGIBLE)"),
              "historical_candidate_frame_px": [1313.5, 332.333]}
    c13 = r13.get("candidate", {}).get("frame_px") if r13.get("candidate") else None
    record["historical_candidate_consistency"] = {
        "attempt-13": {"historical": hist13,
                       "v8_replay_candidate_frame_px": c13,
                       "identical": c13 == hist13["historical_candidate_frame_px"],
                       "note": ("the historical candidate was NOT used as an input; it is "
                                "only compared against the candidate re-derived by v8 from "
                                "the frame's own OCR and bound geometry")},
        "attempt-19": {"historical": "no candidate was ever produced for this frame by "
                                     "the v7-class locator (attempt-19 stopped at menu "
                                     "observation)",
                       "v8_replay_candidate_frame_px": (
                           record["runs"]["attempt-19-replay-1"].get("candidate", {}).get("frame_px")),
                       "note": "v8 establishes the first machine-derived candidate for "
                               "this historical frame"},
        "attempt-05": {"historical": "v7-class locator REFUSED (MENU_CONTENT_UNEXPECTED, "
                                     "no candidate) on this frame",
                       "v8_replay_candidate_frame_px": (
                           record["runs"]["attempt-05-replay-1"].get("candidate", {}).get("frame_px")),
                       "note": "the false-negative this revision closes"},
    }
    record["notes"].append(
        "Every verdict in this record is OFFLINE and confers NO live click "
        "authorization; the attempt-05 menu may no longer exist, and any future round "
        "must freshly re-verify the live menu under a new owner one-shot authorization.")

    jdump(os.path.join(HERE, "replay-record.json"), record)
    summary = {tag: {"verdict": record["runs"][tag + "-replay-1"]["verdict"],
                     "candidate_app_local_pt": (record["runs"][tag + "-replay-1"]
                                                .get("candidate") or {}).get("app_local_pt"),
                     "byte_identical": det[tag]["byte_identical"]}
               for tag in ("attempt-05", "attempt-13", "attempt-19")}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("binding-corrob mad:", record["attempt-19-window-binding-corrob"]["mad_mean"],
          "pass:", record["attempt-19-window-binding-corrob"]["pass"])


if __name__ == "__main__":
    main()
