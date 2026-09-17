#!/usr/bin/env python3
"""Frozen self-test for the v3 route tools (locate_album_card + verify_album_open +
locate_album_ellipsis).

It renders deterministic synthetic frames that mirror the geometry observed on the real
attempt-04 frame (327x643 window, dark card row at y~430 with light text, light text
dots at x~300), runs each tool as a subprocess with the same interpreter that runs this
script, and asserts the documented verdict and exit code of every refusal path.

No real screen content is used or stored: the fixtures are drawn pixel by pixel.
Usage: /opt/homebrew/bin/python3 selftest/run_selftest.py [--out selftest-summary.json]
Exit code 0 when every case passes, 1 otherwise.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def find_tools_dir(start):
    """The directory that holds the frozen tool scripts themselves."""
    current = start
    while True:
        if os.path.exists(os.path.join(current, "locate_album_card.py")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise SystemExit("locate_album_card.py not found above " + start)
        current = parent


TOOLS = find_tools_dir(HERE)
W, H = 327, 643


def load_font(size=14):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


FONT = load_font()


def card_frame(title="2024/05/13~05/17", count="57", strip=(428, 464), bg=200,
               strip_value=46, ink=255):
    im = Image.new("L", (W, H), bg)
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, strip[0], W - 1, strip[1] - 1], fill=strip_value)
    bbox = None
    if title:
        bbox = list(draw.textbbox((17, 432), title, font=FONT))
        draw.text((17, 432), title, font=FONT, fill=ink)
    if count:
        draw.text((17, 448), count, font=FONT, fill=ink)
    return im, bbox


def album_frame(title="2024/05/13~05/17", dots=(), dot_cx=300, dot_cy=47, grid=True):
    im = Image.new("L", (W, H), 120)
    draw = ImageDraw.Draw(im)
    if grid:
        for y in range(100, 620, 32):
            for x in range(0, W, 32):
                draw.rectangle([x, y, x + 15, y + 15], fill=200)
    draw.rectangle([0, 30, W - 1, 60], fill=46)
    bbox = None
    if title:
        bbox = list(draw.textbbox((17, 32), title, font=FONT))
        draw.text((17, 32), title, font=FONT, fill=255)
    for cx in dots:
        for cy in (dot_cy - 5, dot_cy, dot_cy + 5):
            draw.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=200)
    return im, bbox


def group_dot_frame():
    im, bbox = album_frame(dots=(), grid=False)
    draw = ImageDraw.Draw(im)
    for cy in (7, 12, 17):
        draw.rectangle([299, cy - 1, 301, cy + 1], fill=200)
    return im, bbox


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = proc.stdout.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {"_unparsed_stdout": text[-400:],
                   "_stderr": proc.stderr.decode("utf-8", errors="replace")[-400:]}
    return proc.returncode, payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "selftest-summary.json"))
    args = ap.parse_args()
    fixtures = tempfile.mkdtemp(prefix="v3selftest_")
    interpreter = sys.executable
    summary = {"tool": "v3-selftest", "interpreter": interpreter,
               "interpreter_version": sys.version.split()[0],
               "fixtures_dir": fixtures, "cases": []}

    def save(name, image):
        path = os.path.join(fixtures, name + ".png")
        image.save(path)
        return path

    card_ok, card_bbox = card_frame()
    card_pre = save("card_ok", card_ok)
    save("card_notitle", card_frame(title=None)[0])
    save("card_count58", card_frame(count="58")[0])
    save("card_tight", card_frame(strip=(434, 450))[0])
    album_ok, album_bbox = album_frame(dots=(300,))
    album_ok_path = save("album_open", album_ok)
    save("album_open_nodots", album_frame(dots=())[0])
    save("album_open_twodots", album_frame(dots=(300, 260))[0])
    save("album_open_mismatch", album_frame(title="2024/06/01~06/05", dots=(300,))[0])
    save("album_open_notext", album_frame(title=None, dots=(300,))[0])
    group_frame, group_bbox = group_dot_frame()
    group_frame_path = save("album_open_groupdots", group_frame)
    title_bbox_arg = ",".join(str(v) for v in album_bbox)
    group_bbox_arg = "17,2,120,22"

    cases = [
        {"name": "card_ok", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_card.py"), card_pre,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "card_notitle", "expect_exit": 2, "expect_verdict": "TARGET_TITLE_NOT_FOUND",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_card.py"),
                 os.path.join(fixtures, "card_notitle.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "card_count58", "expect_exit": 5, "expect_verdict": "TARGET_COUNT_MISMATCH",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_card.py"),
                 os.path.join(fixtures, "card_count58.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "card_tight_margins", "expect_exit": 4, "expect_verdict": "UNSAFE_MARGINS",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_card.py"),
                 os.path.join(fixtures, "card_tight.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "verify_open", "expect_exit": 0, "expect_verdict": "ALBUM_OPEN_VERIFIED",
         "cmd": [interpreter, os.path.join(TOOLS, "verify_album_open.py"), card_pre,
                 album_ok_path, "--expect-start", "2024/05/13",
                 "--expect-end", "2024/05/17", "--expect-count", "57"]},
        {"name": "verify_no_effect", "expect_exit": 3, "expect_verdict": "NO_EFFECT",
         "cmd": [interpreter, os.path.join(TOOLS, "verify_album_open.py"), card_pre,
                 card_pre, "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "verify_target_mismatch", "expect_exit": 4, "expect_verdict": "TARGET_MISMATCH",
         "cmd": [interpreter, os.path.join(TOOLS, "verify_album_open.py"), card_pre,
                 os.path.join(fixtures, "album_open_mismatch.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "verify_inconclusive", "expect_exit": 5, "expect_verdict": "INCONCLUSIVE",
         "cmd": [interpreter, os.path.join(TOOLS, "verify_album_open.py"), card_pre,
                 os.path.join(fixtures, "album_open_notext.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "ellipsis_one_dot_control", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_click": [300, 47],
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_ellipsis.py"), album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg]},
        {"name": "ellipsis_ocr_derived_title", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_click": [300, 47],
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_ellipsis.py"), album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "ellipsis_two_in_band", "expect_exit": 4, "expect_verdict": "AMBIGUOUS_ELLIPSIS",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_ellipsis.py"),
                 os.path.join(fixtures, "album_open_twodots.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg]},
        {"name": "ellipsis_group_level_only", "expect_exit": 5, "expect_verdict": "GROUP_LEVEL_ONLY",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_ellipsis.py"), group_frame_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--group-title-bbox", group_bbox_arg]},
        {"name": "ellipsis_none", "expect_exit": 3, "expect_verdict": "NO_ELLIPSIS_FOUND",
         "cmd": [interpreter, os.path.join(TOOLS, "locate_album_ellipsis.py"),
                 os.path.join(fixtures, "album_open_nodots.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg]},
    ]

    failures = 0
    for case in cases:
        code, payload = run(case["cmd"])
        checks = {
            "exit": code == case["expect_exit"],
            "verdict": payload.get("verdict") == case["expect_verdict"],
        }
        if "expect_click" in case:
            click = payload.get("click_point")
            ok = isinstance(click, list) and len(click) == 2 and all(
                abs(click[i] - case["expect_click"][i]) <= 2 for i in range(2))
            checks["click_point"] = ok
        passed = all(checks.values())
        if not passed:
            failures += 1
        summary["cases"].append({
            "name": case["name"], "passed": passed, "checks": checks,
            "exit": code, "expect_exit": case["expect_exit"],
            "verdict": payload.get("verdict"), "expect_verdict": case["expect_verdict"],
            "click_point": payload.get("click_point"),
            "count_text": payload.get("count_text") or payload.get("count_digits_read"),
            "detail": None if passed else {
                "stdout_tail": payload.get("_unparsed_stdout"),
                "stderr_tail": payload.get("_stderr"),
            },
        })
    summary["cases_total"] = len(cases)
    summary["cases_failed"] = failures
    summary["result"] = "PASS" if failures == 0 else "FAIL"
    payload = json.dumps(summary, ensure_ascii=False, indent=1)
    print(payload)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload + "\n")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
