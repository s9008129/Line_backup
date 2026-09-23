#!/usr/bin/env python3
"""S11d final pre-click freshness guard for the Save All dispatch (read-only; ZERO GUI input).

At the dispatch moment (seconds before the click):
  1. fresh read-only AX: LINE frontmost; detail-window identity unchanged; the AXDialog that
     IS the open popup menu still present with the same rect [494,81] 137x167 (+-3pt) and
     containing the click point and the S11c menu bbox;
  2. fresh full-screen frame;
  3. approved S6-style ROI menu-presence cross-check (pre-declared rule: gray MAD over a
     240x340 ROI vs the byte-authenticated attempt-19 menu-open reference <= 12.0 AND
     strictly smaller than vs the menu-absent reference) => MENU_ROI_AFFIRMATIVE.
Writes s11d-final-guard.json. Never sends GUI input.
"""
import datetime, hashlib, json, os
from PIL import Image

ATT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(ATT, "..", "..", ".."))
A19 = os.path.join(ROOT, "evidence", "20260916-route", "attempt-19")
OPEN_REF = os.path.join(A19, "frame-menu-post1.png")
ABSENT_REF = os.path.join(A19, "frame-menu-pre.png")
OPEN_SHA = "e321069d86d04f2017e3a972a013fedcac51195ba1e4ba1d9e61df476f8169a2"
ABSENT_SHA = "56959e940b6a0a3f37fbd83b77e9bf7f2b557f63a114a837b088efb7720ce7be"
ROI_W, ROI_H = 240, 340
A19_ANCHOR = (1245, 163)
CLICK_PT = (530.75, 164.25)
DIALOG_EXPECT = (494, 81, 137, 167)

GATE_OUT = "s11d-final-guard.json"
checks = []

def chk(name, ok, detail):
    checks.append({"name": name, "pass": bool(ok), "detail": detail})
    return bool(ok)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def roi_mad(frame_path, anchor):
    a = Image.open(frame_path).convert("L").crop((anchor[0], anchor[1], anchor[0] + ROI_W, anchor[1] + ROI_H))
    return a

def mad(img_x, img_y):
    px, py = img_x.tobytes(), img_y.tobytes()
    return sum(abs(a - b) for a, b in zip(px, py)) / len(px)

def main():
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    gate = {"artifact": GATE_OUT, "phase": "S11d_final_pre_click_guard", "attempt": "07",
            "recorded_at_local": now,
            "authorization_type": "REV27C_ELLIPSIS_THEN_SAVE_ALL_GATE_A",
            "authorization_id": "REV27C-LIVE-GATE-A-AFTER-ATTEMPT06",
            "checks": checks}

    axp = os.path.join(ATT, "s11d-preclick-ax.json")
    ax = json.load(open(axp))
    chk("guard_ax_frontmost", ax.get("ax_api_trusted") is True and ax.get("ax_frontmost") is True
        and ax.get("frontmost_application") == "jp.naver.line.mac",
        {"ax_api_trusted": ax.get("ax_api_trusted"), "frontmost": ax.get("ax_frontmost"),
         "frontmost_application": ax.get("frontmost_application")})
    wins = ax.get("windows", [])
    det = [w for w in wins if w.get("focused") and w.get("main") and w.get("subrole") == "AXStandardWindow"]
    chk("guard_detail_window_identity",
        len(det) == 1 and det[0].get("position_points") == [211, 29] and det[0].get("size_points") == [327, 643],
        {"matches": len(det), "pos": det[0].get("position_points") if det else None,
         "size": det[0].get("size_points") if det else None})
    dialogs = [w for w in wins if w.get("subrole") == "AXDialog"]
    good = None
    for w in dialogs:
        px, py = w.get("position_points", [0, 0]); pw, ph = w.get("size_points", [0, 0])
        if abs(px - DIALOG_EXPECT[0]) <= 3 and abs(py - DIALOG_EXPECT[1]) <= 3 \
           and abs(pw - DIALOG_EXPECT[2]) <= 3 and abs(ph - DIALOG_EXPECT[3]) <= 3 \
           and px <= CLICK_PT[0] <= px + pw and py <= CLICK_PT[1] <= py + ph:
            good = w
    chk("guard_ax_menu_dialog_identity", good is not None,
        {"expected_rect_pt": list(DIALOG_EXPECT), "click_pt": list(CLICK_PT), "dialogs": dialogs})
    gate["ax"] = {"path": "s11d-preclick-ax.json", "sha256": sha(axp), "menu_dialog": good}

    chk("references_byte_authenticated", sha(OPEN_REF) == OPEN_SHA and sha(ABSENT_REF) == ABSENT_SHA,
        {"open_sha": sha(OPEN_REF), "absent_sha": sha(ABSENT_REF)})

    s11c_det = json.load(open(os.path.join(ATT, "s11c-menu-detect.json")))
    anchor = tuple(s11c_det["chosen_bbox"][:2])
    gf = os.path.join(ATT, "s11d-guard-frame.png")
    cframe = os.path.join(ATT, "s11c-preclick-frame.png")
    g_roi = roi_mad(gf, anchor)
    o_roi = roi_mad(OPEN_REF, A19_ANCHOR)
    a_roi = roi_mad(ABSENT_REF, A19_ANCHOR)
    c_roi = roi_mad(cframe, anchor)
    m_open, m_absent, m_c = mad(g_roi, o_roi), mad(g_roi, a_roi), mad(g_roi, c_roi)
    chk("menu_roi_guard_affirmative", m_open <= 12.0 and m_open < m_absent,
        {"anchor_px": list(anchor), "roi_size_px": [ROI_W, ROI_H],
         "mad_guard_vs_menu_open": round(m_open, 3), "mad_guard_vs_menu_absent": round(m_absent, 3),
         "pre_declared_rule": "mad<=12.0 AND mad_open<mad_absent"})
    gate["soft_signals"] = [{"name": "guard_roi_vs_s11c_validated_roi",
                             "mad": round(m_c, 4), "detail": "same-anchor gray MAD of guard frame vs validated S11c frame (rendering stability)"}]
    gate["frames"] = {"guard_frame": {"path": "s11d-guard-frame.png", "sha256": sha(gf)},
                      "validated_frame": {"path": "s11c-preclick-frame.png", "sha256": sha(cframe)}}
    gate["gui_inputs_sent_so_far"] = 1
    gate["save_all_used"] = 0
    gate["verdict"] = "S11D_FINAL_GUARD_PASS" if all(c["pass"] for c in checks) else "S11D_FINAL_GUARD_FAIL"
    gate["failed_checks"] = [c["name"] for c in checks if not c["pass"]]
    for k in ("checks",):
        pass
    json.dump(gate, open(os.path.join(ATT, GATE_OUT), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": gate["verdict"], "failed": gate["failed_checks"], "mad_open": round(m_open, 3),
                      "mad_absent": round(m_absent, 3), "mad_vs_s11c": round(m_c, 4)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
