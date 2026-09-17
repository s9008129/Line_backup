#!/usr/bin/env python3
"""Deterministic selftest matrix for detect_menu_popup.py.

Cases (all synthetic fixtures, no GUI, no screenshots):
  1 positive          : new popup rectangle + >=2 transcribed strings -> exit 0 / MENU_DETECTED
  2 neg_hover         : hover halo only, geometry below rule          -> exit 3 / NOT_DETECTED
  3 neg_identical     : same frame twice                              -> exit 3 / NOT_DETECTED
  4 fail_closed_no_ocr: tesseract unavailable (PATH stripped)         -> exit 3 / OCR_FAILED, no crash
  5 bad_input_missing : missing pre file                              -> exit 6 / BAD_INPUT
  6 bad_input_size    : pre/post size mismatch                        -> exit 6 / BAD_INPUT

Writes selftest-summary.json next to this script. Exit 0 only if every case matches.
"""
import json
import os
import subprocess
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.normpath(os.path.join(HERE, os.pardir, "detect_menu_popup.py"))  # frozen layout: tool lives one level above selftest/
PY = sys.executable


def run(args, env=None):
    env = dict(os.environ if env is None else env)
    proc = subprocess.run([PY] + args, capture_output=True, cwd=HERE, env=env)
    payload = None
    try:
        payload = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        payload = None
    return proc.returncode, payload, proc.stderr.decode("utf-8", errors="replace")


def main():
    mismatched = os.path.join(HERE, "_tmp_mismatch.png")
    Image.new("L", (399, 700), 30).save(mismatched)

    env_no_tess = dict(os.environ)
    env_no_tess["PATH"] = "/nonexistent"

    cases = [
        ("positive", ["fixture-base.png", "fixture-post-menu.png"], 0, "MENU_DETECTED", "OK"),
        ("neg_hover", ["fixture-base.png", "fixture-post-hover.png"], 3, "NOT_DETECTED", None),
        ("neg_identical", ["fixture-base.png", "fixture-base.png"], 3, "NOT_DETECTED", None),
        ("fail_closed_no_ocr", ["fixture-base.png", "fixture-post-menu.png"], 3, "NOT_DETECTED", "OCR_FAILED"),
        ("bad_input_missing", ["fixture-does-not-exist.png", "fixture-base.png"], 6, "BAD_INPUT", None),
        ("bad_input_size", ["fixture-base.png", "_tmp_mismatch.png"], 6, "BAD_INPUT", None),
    ]
    results = []
    all_ok = True
    for name, args, want_rc, want_verdict, want_ocr in cases:
        env = env_no_tess if name == "fail_closed_no_ocr" else None
        rc, payload, stderr = run([TOOL] + args, env=env)
        got_verdict = (payload or {}).get("verdict")
        got_ocr = (payload or {}).get("ocr_status")
        ok = (rc == want_rc and got_verdict == want_verdict and got_ocr == want_ocr)
        all_ok = all_ok and ok
        results.append({"case": name, "args": args, "expected": {"exit": want_rc, "verdict": want_verdict,
                                                                 "ocr_status": want_ocr},
                        "observed": {"exit": rc, "verdict": got_verdict, "ocr_status": got_ocr,
                                     "ocr_strings": (payload or {}).get("ocr_strings"),
                                     "chosen_bbox": (payload or {}).get("chosen_bbox"),
                                     "reason": (payload or {}).get("reason")},
                        "stderr_tail": stderr.strip().splitlines()[-1] if stderr.strip() else None,
                        "ok": ok})
    os.unlink(mismatched)
    summary = {"tool": "detect_menu_popup", "tool_sha256": __import__("hashlib").sha256(
        open(TOOL, "rb").read()).hexdigest(), "cases": results, "all_ok": all_ok}
    with open(os.path.join(HERE, "selftest-summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for item in results:
        print(item["case"], "ok" if item["ok"] else "MISMATCH", item["observed"])
    print("ALL_OK" if all_ok else "FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
