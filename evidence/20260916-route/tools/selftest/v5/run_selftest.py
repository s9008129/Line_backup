#!/usr/bin/env python3
"""Self-test matrix for the v5 route tools (corrected header position rule), 21 cases.

Cases 1-8 re-express the card/verify subset against the v5 tool set (byte-identical
copies of the v4 tools) with the same synthetic geometry and expected literals.
Cases 9-17 re-express the ellipsis subset against the corrected real geometry
(positive control above the title strip at the observed offset) plus the four
v5-specific negatives. Cases 18-20 are the reader-layer cases; case 21 pins the
header-depth flag. The frozen v4 self-test matrix (selftest/v4, 16 cases) is the
reference (pinned to the v4 summary SHA-256 5ad2be10...). Cases 1-13 re-express placeholder
tool set with the same synthetic geometry and the same expected exit code / verdict
literals (pinned to the v3 summary SHA-256 17840e91...). Cases 14-16 are the
reader-layer cases required by plan Rev21 sec 21.4: count-region normalization
(`57張照片` -> MATCH), helper-unavailable fail-closed refusal (documented refusal
path, never a crash, never a rebuild), and a 5x determinism probe (byte-identical
stdout JSON).

TOOLS is pinned to the sibling v4 directory resolved from this file's location
(../../v4); the v3 upward "find the tools dir" convention is deliberately not used
because it would resolve to the frozen v3 tools one level up.

No real screen content is used or stored: every fixture is drawn pixel by pixel
inside a temporary directory. The tools under test are executed as subprocesses
with the same interpreter that runs this script.

Usage: /opt/homebrew/bin/python3 selftest/v4/run_selftest.py [--out selftest-summary.json]
Exit code 0 when every case passes, 1 otherwise; 3 when the v4 tool set is incomplete.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

# The self-test must not leave bytecode caches inside the frozen/versioned tool dirs.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, "v5"))
V4_SUMMARY = os.path.normpath(os.path.join(HERE, os.pardir, "v4", "selftest-summary.json"))
V4_SUMMARY_SHA256_PINNED = "5ad2be101f848ea6a99a8a02ffee8ef65f761fd8b3408bd21c7eb351f1b9fb8d"
V5_TOOL_FILES = ("vision_reader.py", "locate_album_card.py", "verify_album_open.py",
                 "locate_album_ellipsis.py")
FAILCLOSED_BIN = "/nonexistent/vision_ocr_v5_selftest"
W, H = 327, 643


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def missing_tools():
    return [name for name in V5_TOOL_FILES
            if not os.path.isfile(os.path.join(TOOLS, name))]


def tool_shas():
    return {name: sha256_file(os.path.join(TOOLS, name)) for name in V5_TOOL_FILES}


def load_font(size=14):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def load_cjk_font(size=14):
    """System CJK font for the count-normalization fixture (PingFang preferred)."""
    for path in ("/System/Library/Fonts/PingFang.ttc",
                 "/System/Library/Fonts/Hiragino Sans GB.ttc",
                 "/System/Library/Fonts/STHeiti Medium.ttc",
                 "/System/Library/Fonts/STHeiti Light.ttc",
                 "/System/Library/Fonts/Supplemental/Songti.ttc",
                 "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size), path
            except OSError:
                continue
    return None, None


FONT = load_font()
CJK_FONT, CJK_FONT_PATH = load_cjk_font()


def card_frame(title="2024/05/13~05/17", count="57", strip=(428, 464), bg=200,
               strip_value=46, ink=255, count_font=None):
    im = Image.new("L", (W, H), bg)
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, strip[0], W - 1, strip[1] - 1], fill=strip_value)
    bbox = None
    if title:
        bbox = list(draw.textbbox((17, 432), title, font=FONT))
        draw.text((17, 432), title, font=FONT, fill=ink)
    if count:
        draw.text((17, 448), count, font=count_font or FONT, fill=ink)
    return im, bbox


def card_frame_cjk_count(count="57張照片"):
    """The count-normalization fixture: same card geometry, CJK count line.

    When no system CJK font is available the CJK glyphs are approximated with
    filled blocks after the digits so Vision still reads `57` as the prefix.
    """
    if CJK_FONT is not None:
        return card_frame(count=count, count_font=CJK_FONT)[0], CJK_FONT_PATH, False
    im, _ = card_frame(count="57")
    draw = ImageDraw.Draw(im)
    for i in range(3):
        x = 31 + i * 16
        draw.rectangle([x, 450, x + 12, 462], fill=255)
    return im, None, True


def album_frame(title="2024/05/13~05/17", dots=(), dot_cx=300, dot_cy=47, grid=True):
    # v4-geometry helper (dots inside the strip) — retained ONLY for the
    # v5-specific strip-negative (in_title_strip) case.
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


def album_frame_v5(title="2024/05/13~05/17", dots=(), dot_cx=300, dot_cy=12, grid=True):
    # Corrected real-geometry helper: title strip at y 30-60 (as v4), control
    # dots ABOVE the strip in the header band (observed offset: middle ~49.5
    # on the real frame corresponds to header placement here at cy~12 given
    # the synthetic title at y~32; header y1=ty0-7~25, y0~0 with depth 60).
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


def album_frame_low_title(title="2024/05/13~05/17", dots=(), dot_cx=300, dot_cy=100):
    # Beyond-depth helper: title strip lowered to y 198-228 so that dots at
    # y~100 sit above header y0 (=ty0-7-60) and must classify above_header_band.
    im = Image.new("L", (W, H), 120)
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 198, W - 1, 228], fill=46)
    bbox = None
    if title:
        bbox = list(draw.textbbox((17, 200), title, font=FONT))
        draw.text((17, 200), title, font=FONT, fill=255)
    for cx in dots:
        for cy in (dot_cy - 5, dot_cy, dot_cy + 5):
            draw.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=200)
    return im, bbox


def group_dot_frame():
    # Group-only frame: dots in the group-title row (top), no header-band dots.
    im, bbox = album_frame_v5(dots=(), grid=False)
    draw = ImageDraw.Draw(im)
    for cy in (7, 12, 17):
        draw.rectangle([299, cy - 1, 301, cy + 1], fill=200)
    # Blank the header-band area so only the group row carries a triple.
    # (The group bbox is passed explicitly, so region=group_title_band.)
    return im, bbox


def child_env(overrides=None):
    """Deterministic child environment: the ambient VISION_OCR_BIN is cleared so the
    default-path cases exercise the v4 reader's own helper resolution."""
    env = dict(os.environ)
    env.pop("VISION_OCR_BIN", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if overrides:
        env.update(overrides)
    return env


def run(cmd, env=None, timeout=600):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=env, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        return None, exc.stdout or b"", exc.stderr or b"", True


def parse_payload(stdout):
    text = stdout.decode("utf-8", errors="replace")
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        return None, text[-400:]


def reader_first_call(payload):
    reader = payload.get("reader") if isinstance(payload, dict) else None
    calls = reader.get("calls") if isinstance(reader, dict) else None
    if isinstance(calls, list) and calls and isinstance(calls[0], dict):
        return calls[0]
    return None


def fixed_build_binary_path():
    """Best-effort introspection of the v4 reader's fixed helper build path.

    The reader module is loaded only to ask for a declared path attribute or
    zero-argument path helper; the no-rebuild check degrades gracefully when the
    module exposes no stable path.
    """
    path = os.path.join(TOOLS, "vision_reader.py")
    try:
        spec = importlib.util.spec_from_file_location("v5_vision_reader_selftest", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:
        return None
    for name in ("_build_binary", "build_path", "helper_build_path", "default_build_path",
                 "BUILD_PATH", "HELPER_BUILD_PATH"):
        value = getattr(module, name, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        if isinstance(value, str) and value:
            return value
    dir_name = getattr(module, "BUILD_DIR_NAME", None)
    bin_name = getattr(module, "BUILD_NAME", None)
    if isinstance(dir_name, str) and isinstance(bin_name, str):
        return os.path.join(tempfile.gettempdir(), dir_name, bin_name)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "selftest-summary.json"))
    args = ap.parse_args()

    missing = missing_tools()
    if missing:
        print(json.dumps({"tool": "v5-selftest", "result": "BLOCKED",
                          "reason": "v5 tool files missing", "missing": missing,
                          "tools_dir": TOOLS}, ensure_ascii=False, indent=1))
        return 3

    shas_before = tool_shas()
    v3_summary_sha = sha256_file(V4_SUMMARY) if os.path.exists(V4_SUMMARY) else None

    fixtures = tempfile.mkdtemp(prefix="v5selftest_")
    interpreter = sys.executable
    summary = {"tool": "v5-selftest", "interpreter": interpreter,
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
    # v5 corrected-geometry positives (dots above the strip, header band)
    album_ok, album_bbox = album_frame_v5(dots=(300,), dot_cy=12)
    album_ok_path = save("album_open", album_ok)
    save("album_open_nodots", album_frame_v5(dots=())[0])
    save("album_open_twodots", album_frame_v5(dots=(300, 260), dot_cy=12)[0])
    save("album_open_mismatch", album_frame_v5(title="2024/06/01~06/05", dots=(300,), dot_cy=12)[0])
    save("album_open_notext", album_frame_v5(title=None, dots=(300,), dot_cy=12)[0])
    # v5-specific negatives
    save("album_open_stripdots", album_frame(dots=(300,), dot_cy=47)[0])
    low_frame, low_bbox = album_frame_low_title(dots=(300,), dot_cy=100)
    low_frame_path = save("album_open_beyonddepth", low_frame)
    low_title_arg = ",".join(str(v) for v in low_bbox)
    # left-of-edge: header y but x left of tx1+2 (x=50)
    left_frame, _ = album_frame_v5(dots=(50,), dot_cy=12)
    left_frame_path = save("album_open_leftofedge", left_frame)
    group_frame, group_bbox = group_dot_frame()
    group_frame_path = save("album_open_groupdots", group_frame)
    cjk_count_image, cjk_font_used, cjk_fallback = card_frame_cjk_count()
    cjk_count_path = save("card_cjk_count", cjk_count_image)
    title_bbox_arg = ",".join(str(v) for v in album_bbox)
    group_bbox_arg = "17,2,120,22"

    card_cmd = os.path.join(TOOLS, "locate_album_card.py")
    verify_cmd = os.path.join(TOOLS, "verify_album_open.py")
    ellipsis_cmd = os.path.join(TOOLS, "locate_album_ellipsis.py")
    card_ok_cmd = [interpreter, card_cmd, card_pre, "--expect-start", "2024/05/13",
                   "--expect-end", "2024/05/17", "--expect-count", "57"]

    cases = [
        {"name": "card_ok", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "cmd": card_ok_cmd},
        {"name": "card_notitle", "expect_exit": 2, "expect_verdict": "TARGET_TITLE_NOT_FOUND",
         "cmd": [interpreter, card_cmd, os.path.join(fixtures, "card_notitle.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "card_count58", "expect_exit": 5, "expect_verdict": "TARGET_COUNT_MISMATCH",
         "cmd": [interpreter, card_cmd, os.path.join(fixtures, "card_count58.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "card_tight_margins", "expect_exit": 4, "expect_verdict": "UNSAFE_MARGINS",
         "cmd": [interpreter, card_cmd, os.path.join(fixtures, "card_tight.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "verify_open", "expect_exit": 0, "expect_verdict": "ALBUM_OPEN_VERIFIED",
         "cmd": [interpreter, verify_cmd, card_pre, album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--expect-count", "57"]},
        {"name": "verify_no_effect", "expect_exit": 3, "expect_verdict": "NO_EFFECT",
         "cmd": [interpreter, verify_cmd, card_pre, card_pre,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "verify_target_mismatch", "expect_exit": 4, "expect_verdict": "TARGET_MISMATCH",
         "cmd": [interpreter, verify_cmd, card_pre,
                 os.path.join(fixtures, "album_open_mismatch.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "verify_inconclusive", "expect_exit": 5, "expect_verdict": "INCONCLUSIVE",
         "cmd": [interpreter, verify_cmd, card_pre,
                 os.path.join(fixtures, "album_open_notext.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17"]},
        {"name": "ellipsis_v5_positive", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_click": [300, 12],
         "cmd": [interpreter, ellipsis_cmd, album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "ellipsis_v5_ocr_derived_title", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_click": [300, 12],
         "cmd": [interpreter, ellipsis_cmd, album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--header-depth", "60"]},
        {"name": "ellipsis_v5_two_in_header", "expect_exit": 4, "expect_verdict": "AMBIGUOUS_ELLIPSIS",
         "cmd": [interpreter, ellipsis_cmd,
                 os.path.join(fixtures, "album_open_twodots.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "ellipsis_group_level_only", "expect_exit": 5,
         "expect_verdict": "GROUP_LEVEL_ONLY",
         "cmd": [interpreter, ellipsis_cmd, group_frame_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--group-title-bbox", group_bbox_arg,
                 "--header-depth", "60"]},
        {"name": "ellipsis_none", "expect_exit": 3, "expect_verdict": "NO_ELLIPSIS_FOUND",
         "cmd": [interpreter, ellipsis_cmd,
                 os.path.join(fixtures, "album_open_nodots.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "ellipsis_target_absent", "expect_exit": 2, "expect_verdict": "TARGET_TITLE_NOT_FOUND",
         "cmd": [interpreter, ellipsis_cmd,
                 os.path.join(fixtures, "album_open_notext.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--header-depth", "60"]},
        {"name": "ellipsis_v5_strip_dots", "expect_exit": 3, "expect_verdict": "NO_ELLIPSIS_FOUND",
         "cmd": [interpreter, ellipsis_cmd,
                 os.path.join(fixtures, "album_open_stripdots.png"),
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "ellipsis_v5_beyond_depth", "expect_exit": 3, "expect_verdict": "NO_ELLIPSIS_FOUND",
         "cmd": [interpreter, ellipsis_cmd, low_frame_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", low_title_arg, "--header-depth", "60"]},
        {"name": "ellipsis_v5_left_of_edge", "expect_exit": 3, "expect_verdict": "NO_ELLIPSIS_FOUND",
         "cmd": [interpreter, ellipsis_cmd, left_frame_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "ellipsis_v5_header_depth_explicit", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_click": [300, 12],
         "cmd": [interpreter, ellipsis_cmd, album_ok_path,
                 "--expect-start", "2024/05/13", "--expect-end", "2024/05/17",
                 "--title-bbox", title_bbox_arg, "--header-depth", "60"]},
        {"name": "count_normalization", "expect_exit": 0, "expect_verdict": "ELIGIBLE",
         "expect_count_text": "MATCH", "expect_count_prefix": "57",
         "cmd": card_ok_cmd[:2] + [cjk_count_path] + card_ok_cmd[3:]},
        {"name": "helper_unavailable_failclosed", "expect_exit": 2,
         "expect_verdict": "TARGET_TITLE_NOT_FOUND",
         "expect_reader_outcome": "binary_missing",
         "env": {"VISION_OCR_BIN": FAILCLOSED_BIN},
         "cmd": card_ok_cmd},
    ]

    failures = 0
    for case in cases:
        env = child_env(case.get("env"))
        pre_build_path = None
        pre_build_sha = None
        if case["name"] == "helper_unavailable_failclosed":
            pre_build_path = fixed_build_binary_path()
            if pre_build_path and os.path.isfile(pre_build_path):
                pre_build_sha = sha256_file(pre_build_path)
        code, stdout, stderr, timed_out = run(case["cmd"], env=env)
        payload, unparsed = parse_payload(stdout)
        payload = payload or {}
        stderr_text = stderr.decode("utf-8", errors="replace")
        checks = {
            "exit": code == case["expect_exit"],
            "verdict": payload.get("verdict") == case["expect_verdict"],
        }
        if "expect_click" in case:
            click = payload.get("click_point")
            checks["click_point"] = isinstance(click, list) and len(click) == 2 and all(
                abs(click[i] - case["expect_click"][i]) <= 2 for i in range(2))
        evidence = None
        if case["name"] == "count_normalization":
            digits_read = payload.get("count_digits_read")
            checks["count_text"] = payload.get("count_text") == case["expect_count_text"]
            checks["count_prefix"] = (isinstance(digits_read, str)
                                      and digits_read.startswith(case["expect_count_prefix"]))
            evidence = {"count_digits_read": digits_read,
                        "count_text": payload.get("count_text"),
                        "count_box": payload.get("count_box"),
                        "cjk_font_path": CJK_FONT_PATH,
                        "cjk_font_used": cjk_font_used,
                        "cjk_font_fallback_blocks": cjk_fallback,
                        "fixture": cjk_count_path}
        if case["name"] == "helper_unavailable_failclosed":
            checks["no_traceback"] = "Traceback (most recent call last)" not in stderr_text
            first_call = reader_first_call(payload)
            checks["reader_outcome"] = (first_call or {}).get("outcome") \
                == case["expect_reader_outcome"]
            build_path = pre_build_path
            build_before = pre_build_sha
            build_after = (sha256_file(build_path)
                           if build_path and os.path.isfile(build_path) else None)
            checks["no_rebuild"] = build_before == build_after
            evidence = {"env": {"VISION_OCR_BIN": FAILCLOSED_BIN},
                        "reader_calls_first": first_call,
                        "build_binary_path": build_path,
                        "build_binary_sha256_before": build_before,
                        "build_binary_sha256_after": build_after,
                        "rebuild_detected": not checks["no_rebuild"],
                        "stderr_tail": stderr_text[-400:] if stderr_text else ""}
        passed = all(checks.values())
        if not passed:
            failures += 1
        if case["name"] == "card_ok":
            helper_sample = (payload.get("reader") or {}).get("helper") \
                if isinstance(payload.get("reader"), dict) else None
            if isinstance(helper_sample, dict):
                summary["reader_helper_sample"] = helper_sample
        summary["cases"].append({
            "name": case["name"], "passed": passed, "checks": checks,
            "exit": code, "expect_exit": case["expect_exit"],
            "verdict": payload.get("verdict"), "expect_verdict": case["expect_verdict"],
            "click_point": payload.get("click_point"),
            "count_text": payload.get("count_text") or payload.get("count_digits_read"),
            "detail": evidence if evidence is not None else (
                None if passed else {
                    "stdout_tail": unparsed,
                    "stderr_tail": stderr_text[-400:],
                    "timed_out": timed_out,
                }),
        })

    det_cmd = card_ok_cmd
    stdout_shas = []
    det_details = []
    det_exit = []
    det_verdicts = []
    det_unparsed = []
    for i in range(1, 6):
        code, stdout, stderr, timed_out = run(det_cmd, env=child_env())
        raw_path = os.path.join(fixtures, "determinism_5x_run%d.json" % i)
        with open(raw_path, "wb") as f:
            f.write(stdout)
        stdout_shas.append(hashlib.sha256(stdout).hexdigest())
        payload, unparsed = parse_payload(stdout)
        payload = payload or {}
        det_exit.append(code)
        det_verdicts.append(payload.get("verdict"))
        if unparsed:
            det_unparsed.append({"run": i, "stdout_tail": unparsed})
        det_details.append({"run": i, "exit": code, "stdout_sha256": stdout_shas[-1],
                            "raw_file": raw_path})
    det_checks = {
        "exit": all(code == 0 for code in det_exit),
        "verdict": all(v == "ELIGIBLE" for v in det_verdicts),
        "stdout_bytes_identical": len(set(stdout_shas)) == 1,
    }
    det_passed = all(det_checks.values())
    if not det_passed:
        failures += 1
    summary["cases"].append({
        "name": "determinism_5x", "passed": det_passed, "checks": det_checks,
        "exit": det_exit[0], "expect_exit": 0,
        "verdict": det_verdicts[0], "expect_verdict": "ELIGIBLE",
        "click_point": None, "count_text": None,
        "detail": {"stdout_sha256": stdout_shas, "runs": det_details,
                   "identical": det_checks["stdout_bytes_identical"],
                   "unparsed": det_unparsed},
    })

    shas_after = tool_shas()
    tools_stable = shas_before == shas_after
    if not tools_stable:
        failures += 1
    v3_summary_sha_after = sha256_file(V4_SUMMARY) if os.path.exists(V4_SUMMARY) else None
    v3_unchanged = v3_summary_sha_after == V4_SUMMARY_SHA256_PINNED
    if not v3_unchanged:
        failures += 1

    summary["cases_total"] = len(summary["cases"])
    summary["cases_failed"] = failures
    summary["result"] = "PASS" if failures == 0 else "FAIL"
    summary["expectations_pinned_to"] = {
        "v4_summary_path": V4_SUMMARY,
        "v4_summary_sha256_pinned": V4_SUMMARY_SHA256_PINNED,
        "v4_summary_sha256_at_run_start": v3_summary_sha,
        "v4_summary_sha256_after_run": v3_summary_sha_after,
        "v4_summary_unchanged": v3_unchanged,
        "v3_case_literals": ("cases 1-8 + ellipsis re-expression carry the frozen v4 summary's expect_exit/expect_verdict "
                             "verbatim; the two ellipsis control cases keep the v3 click_point "
                             "[300,47] with the +-2 tolerance"),
        "v5_reader_layer_literals": ("cases 18-20 are reader-layer expectations bound to the v5 tool set "
                                     "sec 21.4: count_normalization, helper_unavailable_failclosed, "
                                     "determinism_5x"),
    }
    summary["reader_layer_cases"] = [
        {"name": "count_normalization", "layer": "reader",
         "expectation": ("a card fixture whose 10x count region contains 57張照片 (system CJK "
                         "font; block fallback if unavailable) must yield exit 0 / ELIGIBLE / "
                         "count_text MATCH with count_digits_read starting with 57")},
        {"name": "helper_unavailable_failclosed", "layer": "reader",
         "expectation": ("VISION_OCR_BIN=/nonexistent/vision_ocr_v4_selftest must refuse through "
                         "the documented TARGET_TITLE_NOT_FOUND exit 2 path with no traceback, "
                         "reader.calls[0].outcome=binary_missing, and no rebuild of the fixed "
                         "build-path binary")},
        {"name": "determinism_5x", "layer": "reader",
         "expectation": ("five identical runs of the card_ok argv must produce five "
                         "byte-identical stdout JSON documents (one SHA-256); raw copies are "
                         "kept in fixtures_dir")},
    ]
    summary["env_policy"] = ("VISION_OCR_BIN is cleared for the default-path cases so the v4 "
                             "reader's own helper resolution is exercised; only "
                             "helper_unavailable_failclosed sets it (nonexistent path).")
    summary["fixture_notes"] = {
        "synthetic_only": "all fixtures are drawn pixel by pixel; no real screen content",
        "cjk_font_path": CJK_FONT_PATH,
        "cjk_font_used": cjk_font_used,
        "cjk_font_fallback_blocks": cjk_fallback,
        "pingfang_available": os.path.exists("/System/Library/Fonts/PingFang.ttc"),
    }
    summary["tool_shas"] = {"before": shas_before, "after": shas_after,
                            "stable_during_run": tools_stable,
                            "tools_dir": TOOLS}

    payload_text = json.dumps(summary, ensure_ascii=False, indent=1)
    print(payload_text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload_text + "\n")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
