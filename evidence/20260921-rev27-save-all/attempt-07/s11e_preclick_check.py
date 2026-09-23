#!/usr/bin/env python3
"""S11c pre-click freshness re-validation for the Save All dispatch (read-only; ZERO GUI input).

At the dispatch moment, re-derives from disk/live-read-only sources:
  fresh read-only AX (frontmost + detail-window identity + menu dialog corroboration),
  fresh full-screen frame, fresh approved menu-detector run on that frame,
  fresh frame-bound geometry, a fresh single v8 Save All locator run,
  accepted-baseline tripwire, staging-empty tripwire, durable-intent hash check.
Writes s11e-final-gate.json. Never sends GUI input. Never modifies frozen artifacts.
"""
import datetime, hashlib, json, os, struct, subprocess, sys

ATT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(ATT, "..", "..", ".."))
TOOLS = os.path.join(ROOT, "evidence", "20260916-route", "tools")
DETECTOR = os.path.join(TOOLS, "detect_menu_popup.py")
V8 = os.path.join(TOOLS, "v8", "locate_save_all_menu_item.py")

FRAME = "s11e-preclick-frame.png"
DET_OUT = "s11e-menu-detect.json"
GEO_OUT = "s11e-menu-frame-geometry.json"
V8_OUT = "s11e-v8-locate-save-all.json"
GATE_OUT = "s11e-final-gate.json"

EXP = {
    "baseline_root": "/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/album-2024-05-13_to_2024-05-17_57",
    "baseline_digest": "b7debe929a24406a44f53708194b644a4811559cf91ad87d5a55e5da91a28fbd",
    "baseline_files": 57,
    "baseline_bytes": 17924900,
    "staging_leaf": "/Users/hsiaojohnny/Downloads/LINE-Backup-PoC/staging/RUN-20260923-111908-01",
    "pre_frame": "frame-s1.png",
    "pre_frame_sha": "ca7e0fc9c640cfebb05b7d5dedf5318137d2db1b30090c5399b3d38d9717d4a6",
    "intent_sha": "bead5155c984c9ba9e8fb68c3a5d71a11088a2b4eed5ad2b0272763ddcaa3325",
    "v8_tool_sha": "c5ad46861706a9a2c1c4d477caeda2a809c87c5488844f14a4d3efb34c668a86",
    "window_pos": [211, 29],
    "window_size": [327, 643],
    "click_local": [320, 135],
    "s11_candidate_local": [319.75, 135.25],
}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

checks = []
soft = []

def chk(name, ok, detail):
    checks.append({"name": name, "pass": bool(ok), "detail": detail})
    return bool(ok)

def baseline_inventory():
    root = EXP["baseline_root"]
    entries, files, total = [], 0, 0
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            st = os.lstat(p)
            rel = os.path.relpath(p, root)
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            entries.append(f"{rel}\t{st.st_size}\t{h}\n")
            files += 1
            total += st.st_size
    entries.sort()
    return {"files": files, "bytes": total, "digest": hashlib.sha256("".join(entries).encode()).hexdigest()}

def main():
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    gate = {"artifact": GATE_OUT, "phase": "S11c_final_freshness_gate_at_dispatch_moment", "attempt": "07",
            "recorded_at_local": now,
            "authorization_type": "REV27C_ELLIPSIS_THEN_SAVE_ALL_GATE_A",
            "authorization_id": "REV27C-LIVE-GATE-A-AFTER-ATTEMPT06",
            "method": "read-only re-derivation at dispatch moment; zero GUI input; fresh AX + fresh frame + fresh detector run + fresh v8 run",
            "checks": checks}

    # 1. fresh read-only AX
    axp = os.path.join(ATT, "s11e-preclick-ax.json")
    ax = json.load(open(axp))
    gate["fresh_ax"] = {"path": "s11e-preclick-ax.json", "sha256": sha256_file(axp),
                        "ax_api_trusted": ax.get("ax_api_trusted"), "frontmost": ax.get("ax_frontmost"),
                        "frontmost_application": ax.get("frontmost_application"), "window_count": ax.get("window_count")}
    chk("ax_trusted_frontmost", ax.get("ax_api_trusted") is True and ax.get("ax_frontmost") is True
        and ax.get("frontmost_application") == "jp.naver.line.mac",
        {"ax_api_trusted": ax.get("ax_api_trusted"), "frontmost": ax.get("ax_frontmost"),
         "frontmost_application": ax.get("frontmost_application")})
    wins = ax.get("windows", [])
    detail = [w for w in wins if w.get("focused") and w.get("main") and w.get("subrole") == "AXStandardWindow"]
    chk("detail_window_identity",
        len(detail) == 1 and detail[0].get("position_points") == EXP["window_pos"] and detail[0].get("size_points") == EXP["window_size"],
        {"matches": len(detail), "pos": detail[0].get("position_points") if detail else None,
         "size": detail[0].get("size_points") if detail else None,
         "expected_pos": EXP["window_pos"], "expected_size": EXP["window_size"]})
    gate["detail_window"] = detail[0] if detail else None

    # 2. fresh frame
    fp = os.path.join(ATT, FRAME)
    fsha = sha256_file(fp)
    with open(fp, "rb") as f:
        head = f.read(33)
    w_, h_ = struct.unpack(">II", head[16:24])
    chk("fresh_frame_valid", os.path.getsize(fp) > 0 and [w_, h_] == [2294, 1490], {"size_px": [w_, h_], "sha256": fsha})
    pre_sha = sha256_file(os.path.join(ATT, EXP["pre_frame"]))
    chk("pre_frame_pinned", pre_sha == EXP["pre_frame_sha"], {"sha256": pre_sha, "expected": EXP["pre_frame_sha"]})

    # 3. fresh detector run
    r = subprocess.run([sys.executable, DETECTOR, EXP["pre_frame"], FRAME, "--out", DET_OUT],
                       cwd=ATT, capture_output=True, text=True)
    open(os.path.join(ATT, DET_OUT + ".stdout"), "w").write(r.stdout)
    open(os.path.join(ATT, DET_OUT + ".stderr"), "w").write(r.stderr)
    det = json.load(open(os.path.join(ATT, DET_OUT)))
    det_ok = chk("menu_detector_fresh",
                 det.get("verdict") == "MENU_DETECTED" and det.get("post") == FRAME and det.get("post_sha256") == fsha,
                 {"verdict": det.get("verdict"), "chosen_bbox": det.get("chosen_bbox"),
                  "returncode": r.returncode, "post_sha256": det.get("post_sha256")})
    bbox = det.get("chosen_bbox")
    gate["menu_detector"] = {"json": DET_OUT, "sha256": sha256_file(os.path.join(ATT, DET_OUT)),
                             "verdict": det.get("verdict"), "chosen_bbox": bbox}

    # 3b. bbox sanity vs fresh window rect
    if det_ok and bbox:
        wx0, wy0 = EXP["window_pos"][0] * 2, EXP["window_pos"][1] * 2
        wx1, wy1 = wx0 + EXP["window_size"][0] * 2, wy0 + EXP["window_size"][1] * 2
        overlap = not (bbox[2] < wx0 or bbox[0] > wx1 or bbox[3] < wy0 or bbox[1] > wy1)
        sane = overlap and 100 <= (bbox[2] - bbox[0]) <= 400 and 120 <= (bbox[3] - bbox[1]) <= 500
        chk("menu_bbox_sanity", sane, {"bbox": bbox, "window_rect_px": [wx0, wy0, wx1, wy1], "overlap": overlap})
        d0 = max(abs(bbox[i] - [1008, 182, 1246, 482][i]) for i in range(4))
        soft.append({"name": "menu_bbox_close_to_s11", "pass": d0 <= 90, "detail": {"max_abs_delta_px": d0}})
    else:
        chk("menu_bbox_sanity", False, {"skipped": "no affirmative detector verdict/bbox"})

    # 3c. AXDialog corroboration
    dialog = None
    if det_ok and bbox:
        bpt = [bbox[0] / 2.0, bbox[1] / 2.0, bbox[2] / 2.0, bbox[3] / 2.0]
        for w in wins:
            if w.get("subrole") == "AXDialog":
                px, py = w.get("position_points", [0, 0])
                pw, ph = w.get("size_points", [0, 0])
                if px - 2 <= bpt[0] and py - 2 <= bpt[1] and px + pw + 2 >= bpt[2] and py + ph + 2 >= bpt[3]:
                    dialog = w
        chk("ax_dialog_contains_menu_bbox", dialog is not None, {"menu_bbox_pt": bpt, "dialog": dialog})
    gate["ax_dialog"] = dialog

    # 4. fresh frame-bound geometry json
    geo = {"artifact": GEO_OUT, "frame_sha256": fsha, "capture_scale": 2,
           "window_index": detail[0].get("index") if detail else None,
           "window_position_points": EXP["window_pos"], "window_size_points": EXP["window_size"],
           "window_point_rect": [EXP["window_pos"][0], EXP["window_pos"][1],
                                 EXP["window_pos"][0] + EXP["window_size"][0],
                                 EXP["window_pos"][1] + EXP["window_size"][1]],
           "provenance": f"fresh read-only AX read at {now} (s11e-preclick-ax.json): detail window main+focused, "
                         f"position {EXP['window_pos']} size {EXP['window_size']}; bound to the S11c fresh frame sha; NOT historical geometry",
           "gui_inputs_sent": 1}
    open(os.path.join(ATT, GEO_OUT), "w").write(json.dumps(geo, ensure_ascii=False, indent=1) + "\n")

    # 5. fresh single v8 run
    if det_ok:
        r2 = subprocess.run([sys.executable, V8, FRAME, "--detector-json", DET_OUT, "--geometry", GEO_OUT, "--out", V8_OUT],
                            cwd=ATT, capture_output=True, text=True)
        open(os.path.join(ATT, V8_OUT + ".stdout"), "w").write(r2.stdout)
        open(os.path.join(ATT, V8_OUT + ".stderr"), "w").write(r2.stderr)
        v8p = os.path.join(ATT, V8_OUT)
        v8 = json.load(open(v8p)) if os.path.exists(v8p) else {}
        chk("v8_fresh_eligible", v8.get("verdict") == "ELIGIBLE" and v8.get("exit_code") == 0 and r2.returncode == 0,
            {"verdict": v8.get("verdict"), "exit_code": v8.get("exit_code"), "returncode": r2.returncode, "reason": v8.get("reason")})
        gate["v8"] = {"json": V8_OUT, "sha256": sha256_file(v8p) if os.path.exists(v8p) else None,
                      "verdict": v8.get("verdict"), "reason": v8.get("reason"),
                      "candidate": v8.get("candidate"), "checks": [{"name": c.get("name"), "pass": c.get("pass")} for c in v8.get("checks", [])]}
        if v8.get("verdict") == "ELIGIBLE":
            allhard = all(c.get("pass") for c in v8.get("checks", []) if c.get("class") == "HARD")
            tgt = [c for c in v8.get("checks", []) if c.get("name") == "target_unique_row"]
            chk("v8_all_hard_checks_pass", allhard and len(tgt) == 1 and tgt[0].get("pass"),
                {"hard_pass": allhard, "check_names": [c.get("name") for c in v8.get("checks", [])]})
            cl = (v8.get("candidate") or {}).get("app_local_pt")
            chk("v8_candidate_stable", bool(cl) and abs(cl[0] - EXP["s11_candidate_local"][0]) <= 1.0
                and abs(cl[1] - EXP["s11_candidate_local"][1]) <= 1.0,
                {"fresh_app_local_pt": cl, "s11_app_local_pt": EXP["s11_candidate_local"]})
            der = v8.get("candidate_derivation") or {}
            xs, ys = der.get("x_safe_frame_px"), der.get("y_safe_frame_px")
            cpx = [(EXP["click_local"][0] + EXP["window_pos"][0]) * 2, (EXP["click_local"][1] + EXP["window_pos"][1]) * 2]
            chk("click_point_in_fresh_safe_regions",
                bool(xs) and bool(ys) and xs[0] <= cpx[0] <= xs[1] and ys[0] <= cpx[1] <= ys[1],
                {"click_frame_px": cpx, "x_safe_frame_px": xs, "y_safe_frame_px": ys, "rule": der.get("rule")})
    else:
        chk("v8_fresh_eligible", False, {"skipped": "menu not affirmatively detected on fresh frame"})

    # 6. baseline tripwire
    inv = baseline_inventory()
    binv = {"artifact": "baseline-inventory-s11e-preclick.json", "recorded_at_local": now,
            "label": "READ_ONLY_ACCEPTED_BASELINE_S11B_PRECLICK", "path": EXP["baseline_root"],
            "method": "sorted 'relpath\\tsize\\tsha256\\n' manifest; sha256 of the concatenated manifest",
            **inv, "expected_digest": EXP["baseline_digest"],
            "match": inv["digest"] == EXP["baseline_digest"] and inv["files"] == EXP["baseline_files"] and inv["bytes"] == EXP["baseline_bytes"],
            "gui_input_count": 1}
    open(os.path.join(ATT, "baseline-inventory-s11e-preclick.json"), "w").write(json.dumps(binv, ensure_ascii=False, indent=1) + "\n")
    chk("baseline_unchanged", binv["match"], {"files": inv["files"], "bytes": inv["bytes"], "digest": inv["digest"]})

    # 7. staging tripwire
    ent = sorted(os.listdir(EXP["staging_leaf"]))
    chk("staging_still_empty", ent == [], {"path": EXP["staging_leaf"], "entries": ent})

    # 8. durable intent hash
    isha = sha256_file(os.path.join(ATT, "save-all-click-intent.json"))
    chk("intent_hash_match", isha == EXP["intent_sha"], {"sha256": isha, "expected": EXP["intent_sha"]})

    gate["soft_signals"] = soft
    gate["gui_inputs_sent_so_far"] = 1
    gate["save_all_used"] = 0
    gate["click_point_app_local_pt"] = EXP["click_local"]
    gate["dispatch_immediately_follows"] = all(c["pass"] for c in checks)
    gate["verdict"] = "S11B_FINAL_GATE_PASS" if gate["dispatch_immediately_follows"] else "S11B_FINAL_GATE_FAIL"
    gate["failed_checks"] = [c["name"] for c in checks if not c["pass"]]
    open(os.path.join(ATT, GATE_OUT), "w").write(json.dumps(gate, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"verdict": gate["verdict"], "failed": gate["failed_checks"],
                      "v8_candidate": (gate.get("v8") or {}).get("candidate"),
                      "menu_bbox": (gate.get("menu_detector") or {}).get("chosen_bbox")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
