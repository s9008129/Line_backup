#!/usr/bin/env python3
"""macOS Vision reader for the v4 route tools (Rev21 REQ-VR-1 / REQ-VR-2).

Given a PIL image, this module renders the requested LANCZOS upscale to a
temporary PNG, runs the frozen Vision helper (source SHA-256 4fc9fa2b…,
`VNRecognizeTextRequest`) and returns the v3-shaped word records
`{text, conf, x, y, w, h}` in original-frame coordinates: x=x0/scale,
y=y0/scale, w=(x1-x0)/scale, h=(y1-y0)/scale. Vision observations are
line-level; the helper's own line boxes are the token unit and no
re-tokenization is performed. TEXT is never rewritten: no case folding, no
width normalization, no merge of 禎 (U+798E) and 楨 (U+6968).

Helper resolution: `$VISION_OCR_BIN` when set (used as-is; an invalid value is
never rebuilt), else `<tempdir>/vision_ocr_v4_build/vision_ocr`, built exactly
once from the frozen Swift source with `swiftc -O` when the binary or its
`source.sha256` sidecar is missing/stale. Builds are atomic (build to
`vision_ocr.tmp<pid>`, then `os.replace`).

Fail-closed: every helper failure (missing binary, build failure, non-zero
exit, timeout, unparsable stdout) yields empty words and one recorded call;
the caller then follows the frozen v3 refusal paths. The module never crashes
and never guesses a value. The record carries no timestamps and no
process-unique paths, so repeated runs on the same input are byte-identical.
"""
import hashlib
import os
import re
import subprocess
import tempfile

from PIL import Image

SOURCE_SHA256 = "4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32"
BUILD_DIR_NAME = "vision_ocr_v4_build"
BUILD_NAME = "vision_ocr"
TIMEOUT_S = 60
EXCERPT_LIMIT = 200

_PX = re.compile(r"^px\[(-?\d+),(-?\d+),(-?\d+),(-?\d+)\]$")
_CONF = re.compile(r"^conf=(\d+(?:\.\d+)?)$")

_STATE = {"helper": None, "usable": False, "reason": "", "calls": []}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _excerpt(data):
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
    return text.strip()[:EXCERPT_LIMIT]


def _build_dir():
    return os.path.join(tempfile.gettempdir(), BUILD_DIR_NAME)


def _build_binary():
    return os.path.join(_build_dir(), BUILD_NAME)


def _sidecar():
    return os.path.join(_build_dir(), "source.sha256")


def _frozen_source():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, os.pardir, "vision", "vision_ocr.swift"))


def _file_fields(path):
    if os.path.isfile(path):
        return sha256_file(path), os.path.getsize(path)
    return None, None


def _sidecar_matches():
    try:
        with open(_sidecar(), "r", encoding="utf-8") as f:
            return f.read().strip() == SOURCE_SHA256
    except OSError:
        return False


def _build_once():
    """Build the helper at the fixed path when needed; returns (usable, reason)."""
    binary = _build_binary()
    if os.path.isfile(binary) and _sidecar_matches():
        return True, ""
    source = _frozen_source()
    if not os.path.isfile(source):
        return False, "frozen source missing: " + source
    if sha256_file(source) != SOURCE_SHA256:
        return False, "frozen source sha256 mismatch: " + source
    try:
        os.makedirs(_build_dir(), exist_ok=True)
    except OSError as exc:
        return False, "build dir error: %s" % exc
    tmp = binary + ".tmp%d" % os.getpid()
    try:
        proc = subprocess.run(["swiftc", "-O", source, "-o", tmp],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return False, "swiftc error: %s" % exc
    if proc.returncode != 0 or not os.path.isfile(tmp):
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False, _excerpt(proc.stderr) or ("swiftc exit %d" % proc.returncode)
    os.replace(tmp, binary)
    try:
        with open(_sidecar(), "w", encoding="utf-8") as f:
            f.write(SOURCE_SHA256 + "\n")
    except OSError as exc:
        return False, "sidecar write error: %s" % exc
    return True, ""


def _resolve_helper():
    """Resolve the helper once per process and cache it for the run."""
    if _STATE["helper"] is not None:
        return
    env = os.environ.get("VISION_OCR_BIN")
    if env:
        helper = {"resolved_from": "env", "binary_path": env}
        usable = os.path.isfile(env)
        reason = "" if usable else "helper binary missing: " + env
    else:
        helper = {"resolved_from": "build_path", "binary_path": _build_binary()}
        usable, reason = _build_once()
    helper["binary_sha256"], helper["binary_bytes"] = _file_fields(helper["binary_path"])
    helper["source_sha256"] = SOURCE_SHA256
    _STATE["helper"] = helper
    _STATE["usable"] = usable
    _STATE["reason"] = reason


def read_words(image, scale):
    """Upscale `image` by `scale` (LANCZOS), read it with the Vision helper and
    return v3-shaped word records in original-frame coordinates.

    Any failure returns an empty list; the call outcome is recorded either way."""
    _resolve_helper()
    call = {"scale": scale, "outcome": None, "exit_code": None, "stderr_excerpt": "",
            "stdout_sha256": sha256_bytes(b""), "stdout_bytes": 0, "lines_parsed": 0}
    _STATE["calls"].append(call)
    if not _STATE["usable"]:
        call["outcome"] = ("binary_missing" if _STATE["helper"]["resolved_from"] == "env"
                           else "build_failed")
        call["stderr_excerpt"] = _excerpt(_STATE["reason"])
        return []
    try:
        with tempfile.TemporaryDirectory(prefix="vision_ocr_v4_") as tmpdir:
            png = os.path.join(tmpdir, "frame.png")
            up = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)),
                              Image.LANCZOS)
            up.save(png, format="PNG")
            try:
                proc = subprocess.Popen([_STATE["helper"]["binary_path"], png],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as exc:
                call["outcome"] = "binary_missing"
                call["stderr_excerpt"] = _excerpt("exec error: %s" % exc)
                return []
            try:
                out, err = proc.communicate(timeout=TIMEOUT_S)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                out, err = b"", b""
                call["outcome"] = "timeout"
                call["stderr_excerpt"] = ""
                return []
    except OSError as exc:
        call["outcome"] = "unparsable"
        call["stderr_excerpt"] = _excerpt("render error: %s" % exc)
        return []
    call["exit_code"] = proc.returncode
    call["stdout_sha256"] = sha256_bytes(out)
    call["stdout_bytes"] = len(out)
    if proc.returncode != 0:
        call["outcome"] = "nonzero_exit"
        call["stderr_excerpt"] = _excerpt(err)
        return []
    if not out:
        call["outcome"] = "ok"
        return []
    words = []
    for line in out.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        px = _PX.match(parts[0])
        conf = _CONF.match(parts[1])
        if not px or not conf or not parts[2]:
            continue
        x0, y0, x1, y1 = (int(px.group(i)) for i in range(1, 5))
        words.append({
            "text": parts[2],
            "conf": float(conf.group(1)),
            "x": x0 / float(scale),
            "y": y0 / float(scale),
            "w": (x1 - x0) / float(scale),
            "h": (y1 - y0) / float(scale),
        })
    call["lines_parsed"] = len(words)
    if not words:
        call["outcome"] = "unparsable"
        call["stderr_excerpt"] = _excerpt(err)
        return []
    call["outcome"] = "ok"
    return words


def record():
    """Reader outcome record for the tool JSON (`"reader"`): helper resolution
    plus one call entry per read, in call order."""
    helper = _STATE["helper"]
    return {"helper": dict(helper) if helper is not None else None,
            "calls": [dict(call) for call in _STATE["calls"]]}
