#!/usr/bin/env python3
"""Agent E2E acceptance runner — Rev21 Vision-reader wave (plan.md §21.5, checks C1-C5).

Stage-04 W6-AGENT-E2E. Deterministic, offline orchestrator:
  * zero GUI input, zero screen capture, zero model/API calls, zero formal-data writes;
  * one append-only attempt directory per run (an existing attempt directory is never
    opened or overwritten);
  * every check runs exactly once per attempt — the runner never retries a check
    inside an attempt;
  * bounded loop: `failures_total` continues across attempts; at 5 cumulative
    failures the loop stops with a recorded `stop_reason` before any further check.

CLI:
    python3 runner/run_agent_e2e.py [--attempt NN] [--out DIR]

Exit codes:
    0  attempt executed; all five checks PASS
    1  attempt executed; result FAIL (one or more checks FAIL)
    2  stopped during preflight (frame SHA mismatch, missing frame, missing v4
       tool, plan pin mismatch) — no check was executed
    3  bounded-loop stop: cumulative failure threshold (5) was already reached,
       or was reached during this attempt; no further check is executed
    4  usage error (bad --attempt, attempt directory already exists)

Judgement rules (pinned by plan.md §21.5; never relaxed ad hoc):
    C1  post frame: v4 locate_album_card `count_digits_read` contains `57`
    C2  per input, 5 repeats: v4 locate_album_card stdout JSON bytes identical
        (SHA-256) and helper stdout identical within the repeats
    C3  pre and post: v4 locate_album_card `title` is non-null on both frames
    C4  v4 verify_album_open on (pre, post) -> `ALBUM_OPEN_VERIFIED`, exit 0,
        recorded next to the frozen v3 result (`TARGET_MISMATCH`, exit 4,
        count read `75`); C4 is DEMONSTRATION_ONLY and never flips the frozen
        verdict, never sets CUA_ROUTE_DECISION, never authorizes any GUI input
    C5  s1 and s2 crops: same rule as C1 (`count_digits_read` contains `57`)
    RV-30-4  3x/6x/10x count sweep raw evidence on the post frame (read value +
        confidence per scale; v4 reader calls are authoritative)
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

# Never let this process write bytecode caches into the frozen v4 tool directory
# (the runner imports v4 modules in-process for supplementary OCR-line evidence).
sys.dont_write_bytecode = True

RUNNER_VERSION = "1.1.0"

TASK_ID = "T20260916-0102-01-line-backup-acceptance"
PLAN_REL = f".agent/tasks/{TASK_ID}/plan.md"
HANDOFF_REL = f".agent/tasks/{TASK_ID}/handoff.md"
PLAN_REVISION_PIN = 21
PLAN_SHA256_PIN = "466bda4ad79897cf5f6395beafc0a70c57d99ed4dc15f4b78328fb5c69b68190"

FRAMES_DIR_REL = "evidence/20260917-vision-reader/frames"
FRAME_PINS = {
    "post": ("route5r_frame_post.jpg",
             "4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3"),
    "pre": ("route5r_frame_pre.jpg",
            "3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531"),
    "s1": ("route5r_probe_crop_s1.png",
           "aea53a0df8c4ef20488446dbccc42fa84ecd72c36aad71d42199f20b9e30f5c3"),
    "s2": ("route5r_probe_crop_s2.png",
           "7b9d0a19323e0f7341d2ee9722415251195531dc067b773f231676729c63721b"),
}

V4_DIR_REL = "evidence/20260916-route/tools/v4"
V4_REQUIRED = ("vision_reader.py", "locate_album_card.py", "verify_album_open.py")
V4_OPTIONAL_INFO = ("locate_album_ellipsis.py", "README.md")
V4_SELFTEST_SUMMARY_REL = "evidence/20260916-route/tools/selftest/v4/selftest-summary.json"

FROZEN_V3_ALBUM_OPEN_REL = "evidence/20260916-route/attempt-05/album-open-verify.json"
FROZEN_V3_ALBUM_OPEN_SHA256 = \
    "ffa5d9633804f819473674f57a9979d56e849882f32dfcfa4a2b5b1326083a9b"
FROZEN_V3_LEDGER_REL = "evidence/20260916-route/attempt-05/run-ledger.json"
FROZEN_V3_EXIT_FALLBACK = 4

EXPECT_START = "2024/05/13"
EXPECT_END = "2024/05/17"
EXPECT_COUNT = "57"

C2_REPEATS = 5
C2_INPUTS = ("post", "pre", "s1", "s2")
SWEEP_SCALES = (3, 6, 10)
MAX_CUMULATIVE_FAILURES = 5
CMD_TIMEOUT_S = 240
HELPER_BUILD_TIMEOUT_S = 600

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUT_DIR = REPO_ROOT / "evidence/20260916-route/agent-e2e"

HELPER_LINE_RE = re.compile(r"^px\[(\d+),(\d+),(\d+),(\d+)\]\tconf=([0-9.]+)\t(.*)$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def try_parse_json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def run_command(argv, cwd, timeout=CMD_TIMEOUT_S) -> dict:
    try:
        proc = subprocess.run([str(a) for a in argv], cwd=str(cwd),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout)
        return {"argv": [str(a) for a in argv], "exit_code": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"argv": [str(a) for a in argv], "exit_code": None,
                "stdout": exc.stdout or b"", "stderr": exc.stderr or b"",
                "timed_out": True}
    except OSError as exc:
        return {"argv": [str(a) for a in argv], "exit_code": None,
                "stdout": b"", "stderr": str(exc).encode(), "timed_out": False,
                "error": str(exc)}


def walk_json(obj, path="$"):
    yield path, obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from walk_json(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk_json(value, f"{path}[{index}]")


def extract_stdout_sha_entries(parsed) -> list:
    """Every `stdout_sha256` value found in the tool JSON, in document order."""
    entries = []
    if parsed is None:
        return entries
    for path, node in walk_json(parsed):
        if isinstance(node, dict) and isinstance(node.get("stdout_sha256"), str):
            entries.append({"json_path": f"{path}.stdout_sha256",
                            "value": node["stdout_sha256"]})
    return entries


def extract_helper_hints(parsed) -> list:
    """Candidate helper records (path/sha/size) the tool JSON reports, e.g. the v4
    reader's `{"binary_path": ..., "binary_sha256": ..., "binary_bytes": ...}`."""
    hints = []
    if parsed is None:
        return hints
    for path, node in walk_json(parsed):
        if not isinstance(node, dict):
            continue
        has_sha = any(isinstance(v, str) and HEX64_RE.match(v)
                      for k, v in node.items()
                      if k == "sha256" or k.endswith("_sha256") or k == "sha")
        keyed = any(k in node for k in ("path", "binary", "binary_path", "helper"))
        if has_sha and keyed:
            candidate = {}
            for key, value in node.items():
                if not isinstance(value, (str, int)):
                    continue
                if key in ("path", "binary", "binary_path", "helper", "resolved_from",
                           "size", "bytes") or \
                        key.endswith(("_sha256", "_path", "_bytes", "_size")):
                    candidate[key] = value
            hints.append({"json_path": path, "candidate": candidate})
    return hints


def parse_helper_stdout(raw: bytes, scale: int) -> list:
    words = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        match = HELPER_LINE_RE.match(line)
        if not match:
            continue
        x0, y0, x1, y1 = (int(match.group(i)) for i in range(1, 5))
        words.append({
            "text": match.group(6),
            "conf": float(match.group(5)),
            "x": x0 / float(scale),
            "y": y0 / float(scale),
            "w": (x1 - x0) / float(scale),
            "h": (y1 - y0) / float(scale),
        })
    return words


def digits_of(text: str) -> str:
    return re.sub(r"\D", "", text or "")


# --------------------------------------------------------------------------
# append-only artifact registry
# --------------------------------------------------------------------------
class Artifacts:
    """Every raw artifact goes through this registry so summary.json can list the
    SHA-256 of each of them."""

    def __init__(self, attempt_dir: Path):
        self.attempt_dir = attempt_dir
        self.map = {}

    def write_raw(self, rel: str, data: bytes) -> str:
        path = self.attempt_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        digest = sha256_bytes(data)
        self.map[rel] = digest
        return digest

    def write_json(self, rel: str, obj) -> str:
        return self.write_raw(rel, json_bytes(obj))

    def reconcile_on_disk(self):
        """Guarantee the registry covers exactly what is on disk under raw/."""
        raw_dir = self.attempt_dir / "raw"
        on_disk = {}
        if raw_dir.is_dir():
            for path in sorted(raw_dir.rglob("*")):
                if path.is_file():
                    rel = str(path.relative_to(self.attempt_dir))
                    on_disk[rel] = sha256_file(path)
        missing = sorted(set(self.map) - set(on_disk))
        extra = sorted(set(on_disk) - set(self.map))
        for rel in extra:
            self.map[rel] = on_disk[rel]
        return {"missing_from_disk": missing, "added_from_disk": extra}


# --------------------------------------------------------------------------
# deterministic fallback helper resolution (runner-side probe only)
# --------------------------------------------------------------------------
class DirectHelper:
    """Runner-side Vision helper for the C2 helper-stdout probe and the RV-30-4
    sweep fallback. Resolution mirrors the pinned reader contract:

      1. `$VISION_OCR_BIN` if set: used when valid; when invalid NO rebuild is
         attempted (the pinned fail-closed rule) and the helper is reported
         unavailable;
      2. otherwise `<tempdir>/agent_e2e_vision_ocr`, built once with `swiftc -O`
         from the frozen source and reused afterwards.

    It is read-only, sends no input, and is never used to weaken a judgement:
    the v4 tool JSON is always the primary evidence."""

    BUILD_NAME = "agent_e2e_vision_ocr"

    def __init__(self, repo: Path):
        self.repo = repo
        self.env_value = os.environ.get("VISION_OCR_BIN")
        self.path = None
        self.method = None
        self.build = None
        self.error = None

    def resolve(self):
        if self.method is not None:
            return
        if self.env_value is not None:
            candidate = Path(self.env_value)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                self.path = candidate
                self.method = "env_VISION_OCR_BIN"
            else:
                self.method = "env_set_invalid_no_rebuild"
                self.error = ("VISION_OCR_BIN is set but invalid; no rebuild "
                              "(pinned fail-closed rule)")
            return
        target = Path(tempfile.gettempdir()) / self.BUILD_NAME
        if target.is_file() and os.access(target, os.X_OK):
            self.path = target
            self.method = "temp_build_reused"
            return
        source = self.repo / "evidence/20260916-route/tools/vision/vision_ocr.swift"
        if not source.is_file():
            self.method = "unavailable"
            self.error = f"frozen helper source missing: {source}"
            return
        result = run_command(["swiftc", "-O", str(source), "-o", str(target)],
                             self.repo, timeout=HELPER_BUILD_TIMEOUT_S)
        self.build = {"argv": result["argv"], "exit_code": result["exit_code"],
                      "timed_out": result["timed_out"],
                      "stderr_tail": result["stderr"][-2000:].decode(errors="replace")}
        if result["exit_code"] == 0 and target.is_file():
            self.path = target
            self.method = "temp_build_created"
        else:
            self.method = "unavailable"
            self.error = "swiftc build failed"

    def info(self) -> dict:
        info = {"env_VISION_OCR_BIN": self.env_value,
                "resolution_method": self.method or "unresolved",
                "path": None, "size_bytes": None, "sha256": None,
                "build": self.build}
        if self.path and self.path.is_file():
            info["path"] = str(self.path)
            info["size_bytes"] = self.path.stat().st_size
            info["sha256"] = sha256_file(self.path)
        if self.error:
            info["error"] = self.error
        return info

    def invoke(self, image_path) -> dict:
        if not self.path:
            return {"argv": None, "exit_code": None, "stdout": b"", "stderr": b"",
                    "timed_out": False, "error": self.error or "helper unavailable"}
        return run_command([str(self.path), str(image_path)], self.repo)

    def render_scale(self, source_path, scale: int, dest_path) -> str:
        from PIL import Image  # lazy: only needed on the fallback path
        image = Image.open(source_path).convert("L")
        upscaled = image.resize((image.size[0] * scale, image.size[1] * scale),
                                Image.LANCZOS)
        upscaled.save(dest_path, format="PNG")
        return str(dest_path)


# --------------------------------------------------------------------------
# run context
# --------------------------------------------------------------------------
class Context:
    def __init__(self, repo: Path, attempt_dir: Path, v4_abs: dict, frames: dict,
                 artifacts: Artifacts):
        self.repo = repo
        self.attempt_dir = attempt_dir
        self.artifacts = artifacts
        self.v4 = v4_abs          # name -> {"rel", "abs", "sha256", "size_bytes"}
        self.frames = frames      # label -> {"rel", "abs", "sha256", "size_bytes"}
        self.direct_helper = DirectHelper(repo)
        self.python = sys.executable
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent_e2e_"))
        self.card_module = None
        self.card_module_error = None
        self.helper_hints = []
        self.tool_helper_hint_paths = set()

    # -- v4 CLI argv builders (identical path strings across repeats) ------
    def card_argv(self, frame_rel: str) -> list:
        return [self.python, self.v4["locate_album_card.py"]["rel"], frame_rel,
                "--expect-start", EXPECT_START, "--expect-end", EXPECT_END,
                "--expect-count", EXPECT_COUNT]

    def verify_argv(self, pre_rel: str, post_rel: str) -> list:
        return [self.python, self.v4["verify_album_open.py"]["rel"], pre_rel,
                post_rel, "--expect-start", EXPECT_START, "--expect-end",
                EXPECT_END, "--expect-count", EXPECT_COUNT]

    # -- v4 module access (supplementary raw-line evidence; never gating) --
    def load_card_module(self):
        if self.card_module is not None or self.card_module_error is not None:
            return self.card_module
        path = Path(self.v4["locate_album_card.py"]["abs"])
        try:
            v4_dir = str(path.parent)
            if v4_dir not in sys.path:
                sys.path.insert(0, v4_dir)
            spec = importlib.util.spec_from_file_location(
                "v4_locate_album_card_for_e2e", str(path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.card_module = module
        except Exception as exc:
            self.card_module_error = f"{type(exc).__name__}: {exc}"
        return self.card_module

    def module_ocr_words(self, image, scale: int) -> list:
        module = self.load_card_module()
        if module is None:
            raise RuntimeError(f"v4 locate_album_card not loadable: {self.card_module_error}")
        last_error = None
        for call in (lambda: module.ocr_words(image, scale=scale),
                     lambda: module.ocr_words(image, scale)):
            try:
                words = call()
            except TypeError as exc:
                last_error = exc
                continue
            if isinstance(words, list):
                return words
            last_error = RuntimeError("ocr_words returned a non-list")
        raise RuntimeError(f"v4 ocr_words unavailable: {last_error}")

    def record_helper_hints(self, parsed, source: str):
        for hint in extract_helper_hints(parsed):
            key = (hint["json_path"], json.dumps(hint["candidate"], sort_keys=True))
            if key in self.tool_helper_hint_paths:
                continue
            self.tool_helper_hint_paths.add(key)
            entry = dict(hint)
            entry["source"] = source
            self.helper_hints.append(entry)


# --------------------------------------------------------------------------
# supplementary reader-line evidence (v4 reader calls preferred; helper fallback)
# --------------------------------------------------------------------------
def supplementary_reader_lines(ctx: Context, frame: dict, count_box, raw_prefix: str) -> dict:
    """Full-frame (3x) and count-region (10x) OCR lines with conf + bbox, using
    the v4 reader path when available and the runner's direct helper otherwise."""
    out = {"frame_lines": None, "count_region_lines": None, "method": None,
           "note": "supplementary raw lines for C1/C5 evidence; the tool JSON above "
                   "is the authoritative judgement input"}
    try:
        from PIL import Image
    except Exception as exc:
        out["error"] = f"PIL unavailable: {exc}"
        return out

    image = Image.open(frame["abs"]).convert("L")
    module_lines = None
    module_error = None
    try:
        module_lines = ctx.module_ocr_words(image, 3)
        out["method"] = "v4_locate_album_card.ocr_words"
    except Exception as exc:
        module_error = f"{type(exc).__name__}: {exc}"

    if module_lines is not None:
        out["frame_lines"] = module_lines
        if count_box:
            crop = image.crop(tuple(count_box))
            try:
                out["count_region_lines"] = ctx.module_ocr_words(crop, 10)
            except Exception as exc:
                out["count_region_error"] = f"{type(exc).__name__}: {exc}"
    else:
        ctx.direct_helper.resolve()
        out["method"] = f"runner_direct_helper({ctx.direct_helper.method})"
        out["module_error"] = module_error
        if ctx.direct_helper.path:
            frame_png = ctx.temp_dir / f"frame3x_{frame['rel'].replace('/', '_')}.png"
            ctx.direct_helper.render_scale(frame["abs"], 3, frame_png)
            run = ctx.direct_helper.invoke(frame_png)
            out["frame_lines"] = parse_helper_stdout(run["stdout"], 3)
            out["helper_exit_code"] = run["exit_code"]
            if count_box:
                crop = image.crop(tuple(count_box))
                crop_png = ctx.temp_dir / f"region10x_{frame['rel'].replace('/', '_')}.png"
                crop_upscaled = crop.resize((crop.size[0] * 10, crop.size[1] * 10),
                                            Image.LANCZOS)
                crop_upscaled.save(crop_png, format="PNG")
                run = ctx.direct_helper.invoke(crop_png)
                out["count_region_lines"] = parse_helper_stdout(run["stdout"], 10)
        else:
            out["helper_error"] = ctx.direct_helper.error

    if count_box:
        out["count_box"] = list(count_box)
    ctx.artifacts.write_json(f"{raw_prefix}_reader_lines.json", out)
    return out


def summarize_scale_read(lines: list) -> dict:
    """Read value + confidence for one scale: the line(s) whose digits contain
    the expected count, plus the concatenated digit read of all lines."""
    joined = digits_of("".join(w.get("text", "") for w in lines))
    matches = [{"text": w.get("text"), "digits": digits_of(w.get("text", "")),
                "conf": w.get("conf"), "bbox": [round(w.get("x", 0)), round(w.get("y", 0)),
                                                round(w.get("x", 0) + w.get("w", 0)),
                                                round(w.get("y", 0) + w.get("h", 0))]}
               for w in lines if EXPECT_COUNT in digits_of(w.get("text", ""))]
    best = matches[0] if matches else None
    return {"read": joined, "expected_count_present": EXPECT_COUNT in joined,
            "best_line": best,
            "match_lines": matches,
            "line_count": len(lines)}


def count_sweep(ctx: Context, frame: dict, count_box, raw_prefix: str) -> dict:
    """RV-30-4: 3x/6x/10x count-region and full-frame sweep raw evidence on the
    post frame (read value + conf per scale)."""
    out = {"purpose": "RV-30-4 count sweep (3x/6x/10x) raw evidence",
           "input": frame["rel"], "input_sha256": frame["sha256"],
           "count_box": list(count_box) if count_box else None,
           "frame_reads": {}, "count_region_reads": {},
           "official_count_region_read": None, "method": None}
    try:
        from PIL import Image
    except Exception as exc:
        out["error"] = f"PIL unavailable: {exc}"
        ctx.artifacts.write_json(f"{raw_prefix}_sweep.json", out)
        return out

    image = Image.open(frame["abs"]).convert("L")
    module_ok = False
    try:
        ctx.module_ocr_words(image, 3)
        module_ok = True
    except Exception:
        module_ok = False

    if module_ok:
        out["method"] = "v4_locate_album_card.ocr_words"
        for scale in SWEEP_SCALES:
            lines = ctx.module_ocr_words(image, scale)
            out["frame_reads"][f"{scale}x"] = summarize_scale_read(lines)
            ctx.artifacts.write_json(f"{raw_prefix}_frame_{scale}x_lines.json", lines)
            if count_box:
                crop = image.crop(tuple(count_box))
                crop_lines = ctx.module_ocr_words(crop, scale)
                out["count_region_reads"][f"{scale}x"] = summarize_scale_read(crop_lines)
                ctx.artifacts.write_json(f"{raw_prefix}_region_{scale}x_lines.json", crop_lines)
        if count_box:
            module = ctx.load_card_module()
            try:
                digits = module.ocr_digits_region(image, tuple(count_box), scale=10)
                out["official_count_region_read"] = digits
            except Exception as exc:
                out["official_count_region_error"] = f"{type(exc).__name__}: {exc}"
    else:
        ctx.direct_helper.resolve()
        out["method"] = f"runner_direct_helper({ctx.direct_helper.method})"
        if not ctx.direct_helper.path:
            out["error"] = ctx.direct_helper.error or "helper unavailable"
            ctx.artifacts.write_json(f"{raw_prefix}_sweep.json", out)
            return out
        for scale in SWEEP_SCALES:
            frame_png = ctx.temp_dir / f"sweep_frame_{scale}x.png"
            ctx.direct_helper.render_scale(frame["abs"], scale, frame_png)
            run = ctx.direct_helper.invoke(frame_png)
            lines = parse_helper_stdout(run["stdout"], scale)
            out["frame_reads"][f"{scale}x"] = summarize_scale_read(lines)
            ctx.artifacts.write_json(f"{raw_prefix}_frame_{scale}x_lines.json", lines)
            if count_box:
                crop = image.crop(tuple(count_box))
                crop_png = ctx.temp_dir / f"sweep_region_{scale}x.png"
                crop_upscaled = crop.resize((crop.size[0] * scale, crop.size[1] * scale),
                                            Image.LANCZOS)
                crop_upscaled.save(crop_png, format="PNG")
                run = ctx.direct_helper.invoke(crop_png)
                crop_lines = parse_helper_stdout(run["stdout"], scale)
                out["count_region_reads"][f"{scale}x"] = summarize_scale_read(crop_lines)
                ctx.artifacts.write_json(f"{raw_prefix}_region_{scale}x_lines.json", crop_lines)
    ctx.artifacts.write_json(f"{raw_prefix}_sweep.json", out)
    return out


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def _card_run_entry(ctx: Context, run: dict, raw_rel: str, parsed) -> dict:
    ctx.artifacts.write_raw(raw_rel, run["stdout"])
    return {"argv": run["argv"], "exit_code": run["exit_code"],
            "timed_out": run["timed_out"],
            "parsed_verdict": parsed.get("verdict") if isinstance(parsed, dict) else None,
            "stdout_sha256": sha256_bytes(run["stdout"]),
            "raw_stdout": raw_rel,
            "stderr_tail": run["stderr"][-1000:].decode(errors="replace")}


def check_c1(ctx: Context) -> dict:
    frame = ctx.frames["post"]
    result = {"check_id": "C1",
              "title": "post frame count read (v4 locate_album_card)",
              "judgement_rule": "count_digits_read contains '57'",
              "frame": frame["rel"], "frame_sha256": frame["sha256"]}
    run = run_command(ctx.card_argv(frame["rel"]), ctx.repo)
    parsed = try_parse_json(run["stdout"])
    result["commands"] = [_card_run_entry(ctx, run, "raw/c1_post_stdout.json", parsed)]
    if parsed is None:
        result["pass"] = False
        result["error"] = "v4 locate_album_card stdout is not valid JSON"
        return result
    ctx.record_helper_hints(parsed, "C1 locate_album_card")
    count_box = parsed.get("count_box")
    result["count_digits_read"] = parsed.get("count_digits_read")
    result["count_box"] = count_box
    result["count_text"] = parsed.get("count_text")
    result["title"] = parsed.get("title")
    result["pass"] = EXPECT_COUNT in str(parsed.get("count_digits_read") or "")
    result["reader_lines"] = supplementary_reader_lines(ctx, frame, count_box, "raw/c1")
    result["rv30_4_sweep"] = count_sweep(ctx, frame, count_box, "raw/rv30_4")
    return result


def check_c2(ctx: Context) -> dict:
    result = {"check_id": "C2", "title": "determinism: 5 repeats per input",
              "judgement_rule": "per input: 5 v4 locate_album_card stdout JSON byte-identical "
                                "(SHA-256), and helper stdout identical across the repeats "
                                "(tool-JSON reader stdouts when present; runner direct helper "
                                "probe otherwise)",
              "repeats": C2_REPEATS, "inputs": {}}
    overall_pass = True
    for label in C2_INPUTS:
        frame = ctx.frames[label]
        argv = ctx.card_argv(frame["rel"])
        runs = []
        stdout_shas = []
        reader_sequences = []
        reader_present = False
        for index in range(1, C2_REPEATS + 1):
            run = run_command(argv, ctx.repo)
            parsed = try_parse_json(run["stdout"])
            raw_rel = f"raw/c2/{label}_run{index}_stdout.json"
            digest = sha256_bytes(run["stdout"])
            ctx.artifacts.write_raw(raw_rel, run["stdout"])
            stdout_shas.append(digest)
            entries = extract_stdout_sha_entries(parsed)
            if entries:
                reader_present = True
            reader_sequences.append([entry["value"] for entry in entries])
            if parsed is not None and index == 1:
                ctx.record_helper_hints(parsed, f"C2 {label} run1")
            runs.append({"run": index, "exit_code": run["exit_code"],
                         "timed_out": run["timed_out"],
                         "parsed_verdict": parsed.get("verdict") if parsed else None,
                         "stdout_sha256": digest, "raw_stdout": raw_rel,
                         "reader_stdout_sha256_sequence": reader_sequences[-1]})
        entry = {"runs": runs,
                 "stdout_sha256s": stdout_shas,
                 "stdout_bytes_identical": len(set(stdout_shas)) == 1,
                 "reader_field_present": reader_present,
                 "reader_stdout_sha256_sequences": reader_sequences}
        helper_via_tool = reader_present and \
            all(sequence for sequence in reader_sequences) and \
            len({tuple(sequence) for sequence in reader_sequences}) == 1
        entry["helper_stdout_identical_via_tool_json"] = helper_via_tool

        if not reader_present:
            probe = _direct_helper_probe(ctx, frame, label)
            entry["direct_helper_probe"] = probe
            helper_evidence = probe.get("available", False)
            helper_ok = bool(probe.get("all_equal"))
        else:
            entry["direct_helper_probe"] = None
            helper_evidence = True
            helper_ok = helper_via_tool
        entry["helper_stdout_evidence_available"] = helper_evidence
        entry["helper_stdout_identical"] = helper_ok
        entry["input_pass"] = entry["stdout_bytes_identical"] and helper_ok
        overall_pass = overall_pass and entry["input_pass"]
        result["inputs"][label] = entry
    result["pass"] = overall_pass
    return result


def _direct_helper_probe(ctx: Context, frame: dict, label: str) -> dict:
    """Runner-side 5x helper invocation on the same input (frame rendered at 3x,
    as the reader's frame read does). Raw stdout stored per invocation."""
    probe = {"available": False}
    ctx.direct_helper.resolve()
    probe["helper"] = ctx.direct_helper.info()
    if not ctx.direct_helper.path:
        probe["error"] = ctx.direct_helper.error or "helper unavailable"
        return probe
    from PIL import Image  # noqa: F401  (ensures the render path is possible)
    frame_png = ctx.temp_dir / f"c2_{label}_frame3x.png"
    ctx.direct_helper.render_scale(frame["abs"], 3, frame_png)
    probe["rendered_input"] = str(frame_png)
    probe["rendered_input_sha256"] = sha256_file(frame_png)
    probe["rendered_input_bytes"] = os.path.getsize(frame_png)
    shas = []
    for index in range(1, C2_REPEATS + 1):
        run = ctx.direct_helper.invoke(frame_png)
        raw_rel = f"raw/c2/{label}_helper_run{index}.stdout"
        ctx.artifacts.write_raw(raw_rel, run["stdout"])
        shas.append({"run": index, "exit_code": run["exit_code"],
                     "stdout_sha256": sha256_bytes(run["stdout"]),
                     "raw_stdout": raw_rel})
    probe["available"] = True
    probe["runs"] = shas
    probe["all_equal"] = len({item["stdout_sha256"] for item in shas}) == 1
    return probe


def check_c3(ctx: Context) -> dict:
    result = {"check_id": "C3", "title": "date title on pre and post frames",
              "judgement_rule": "v4 locate_album_card title is non-null on both frames",
              "frames": {}}
    passed = True
    for label in ("pre", "post"):
        frame = ctx.frames[label]
        run = run_command(ctx.card_argv(frame["rel"]), ctx.repo)
        parsed = try_parse_json(run["stdout"])
        entry = _card_run_entry(ctx, run, f"raw/c3_{label}_stdout.json", parsed)
        frame_pass = isinstance(parsed, dict) and isinstance(parsed.get("title"), dict)
        entry["frame_pass"] = frame_pass
        if parsed is not None:
            entry["title"] = parsed.get("title")
            entry["title_texts"] = (parsed.get("title") or {}).get("texts")
            entry["title_bbox"] = (parsed.get("title") or {}).get("bbox")
            joined = digits_of("".join((parsed.get("title") or {}).get("texts") or []))
            entry["derived_digits"] = joined
            entry["derived_start_present"] = digits_of(EXPECT_START) in joined
            entry["derived_end_present"] = any(
                key in joined for key in
                (digits_of(EXPECT_END), digits_of(EXPECT_END)[-4:]))
        result["frames"][label] = entry
        passed = passed and frame_pass
    result["pass"] = passed
    return result


def check_c4(ctx: Context) -> dict:
    result = {"check_id": "C4",
              "title": "frozen S5 replay (DEMONSTRATION_ONLY)",
              "judgement_rule": "v4 verify_album_open on (pre, post) returns "
                                "ALBUM_OPEN_VERIFIED with exit 0",
              "demonstration_only": True,
              "never_flips_frozen_verdict": True,
              "sets_cua_route_decision": False,
              "authorizes_gui": False}
    frozen_path = ctx.repo / FROZEN_V3_ALBUM_OPEN_REL
    frozen = {"path": FROZEN_V3_ALBUM_OPEN_REL, "expected_sha256": FROZEN_V3_ALBUM_OPEN_SHA256}
    if frozen_path.is_file():
        frozen["observed_sha256"] = sha256_file(frozen_path)
        frozen["match"] = frozen["observed_sha256"] == FROZEN_V3_ALBUM_OPEN_SHA256
        parsed_frozen = try_parse_json(frozen_path.read_bytes())
        if isinstance(parsed_frozen, dict):
            frozen["verdict"] = parsed_frozen.get("verdict")
            frozen["count_digits_read"] = parsed_frozen.get("count_digits_read")
            frozen["count_text"] = parsed_frozen.get("count_text")
    else:
        frozen["observed_sha256"] = None
        frozen["match"] = False
        frozen["missing"] = True

    ledger_path = ctx.repo / FROZEN_V3_LEDGER_REL
    frozen["exit_code"] = FROZEN_V3_EXIT_FALLBACK
    frozen["exit_code_source"] = "plan/handoff pin (run-ledger not parsed)"
    if ledger_path.is_file():
        ledger = try_parse_json(ledger_path.read_bytes())
        if isinstance(ledger, dict):
            for event in ledger.get("events", []):
                verify = event.get("verify") if isinstance(event, dict) else None
                if isinstance(verify, dict) and "exit_code" in verify:
                    frozen["exit_code"] = verify["exit_code"]
                    frozen["exit_code_source"] = \
                        f"{FROZEN_V3_LEDGER_REL} events[seq={event.get('seq')}].verify.exit_code"
                    break
    result["frozen_v3_result"] = frozen

    pre = ctx.frames["pre"]
    post = ctx.frames["post"]
    run = run_command(ctx.verify_argv(pre["rel"], post["rel"]), ctx.repo)
    parsed = try_parse_json(run["stdout"])
    entry = _card_run_entry(ctx, run, "raw/c4_stdout.json", parsed)
    result["commands"] = [entry]
    if parsed is not None:
        ctx.record_helper_hints(parsed, "C4 verify_album_open")
        result["verdict"] = parsed.get("verdict")
        result["count_digits_read"] = parsed.get("count_digits_read")
        result["count_text"] = parsed.get("count_text")
        result["target_title_in_post"] = parsed.get("target_title_in_post")
        result["diff_changed_fraction"] = (parsed.get("diff") or {}).get("changed_fraction")
    result["pass"] = bool(parsed is not None
                          and run["exit_code"] == 0
                          and parsed.get("verdict") == "ALBUM_OPEN_VERIFIED")
    if not frozen.get("match"):
        result["stop_request"] = ("FROZEN_V3_ARTIFACT_CHANGED: "
                                  f"{FROZEN_V3_ALBUM_OPEN_REL}")
    ctx.artifacts.write_json("raw/c4_frozen_v3_comparison.json", frozen)
    return result


def check_c5(ctx: Context) -> dict:
    result = {"check_id": "C5", "title": "s1/s2 crop count reads (v4 locate_album_card)",
              "judgement_rule": "count_digits_read contains '57' on both crops",
              "crops": {}}
    passed = True
    for label in ("s1", "s2"):
        frame = ctx.frames[label]
        run = run_command(ctx.card_argv(frame["rel"]), ctx.repo)
        parsed = try_parse_json(run["stdout"])
        entry = _card_run_entry(ctx, run, f"raw/c5_{label}_stdout.json", parsed)
        if parsed is not None:
            entry["count_digits_read"] = parsed.get("count_digits_read")
            entry["count_box"] = parsed.get("count_box")
            entry["count_text"] = parsed.get("count_text")
            entry["title"] = parsed.get("title")
            entry["crop_pass"] = EXPECT_COUNT in str(parsed.get("count_digits_read") or "")
            entry["reader_lines"] = supplementary_reader_lines(
                ctx, frame, parsed.get("count_box"), f"raw/c5_{label}")
        else:
            entry["crop_pass"] = False
            entry["error"] = "v4 locate_album_card stdout is not valid JSON"
        result["crops"][label] = entry
        passed = passed and entry.get("crop_pass", False)
    result["pass"] = passed
    return result


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------
def preflight_frames(repo: Path) -> dict:
    frames = {}
    stop_reason = None
    for label, (filename, pinned) in FRAME_PINS.items():
        path = repo / FRAMES_DIR_REL / filename
        info = {"label": label, "rel": f"{FRAMES_DIR_REL}/{filename}",
                "abs": str(path), "pinned_sha256": pinned}
        if path.is_file():
            info["sha256"] = sha256_file(path)
            info["size_bytes"] = path.stat().st_size
            info["match"] = info["sha256"] == pinned
            if not info["match"] and stop_reason is None:
                stop_reason = (f"FRAME_SHA_MISMATCH({label}): expected {pinned}, "
                               f"observed {info['sha256']}")
        else:
            info["sha256"] = None
            info["match"] = False
            info["missing"] = True
            if stop_reason is None:
                stop_reason = f"FRAME_MISSING({label}): {info['rel']}"
        frames[label] = info
    return {"frames": frames, "stop_reason": stop_reason}


def preflight_v4_tools(repo: Path) -> dict:
    tools = {}
    missing = []
    for name in V4_REQUIRED:
        path = repo / V4_DIR_REL / name
        info = {"name": name, "rel": f"{V4_DIR_REL}/{name}", "abs": str(path),
                "required": True}
        if path.is_file():
            info["sha256"] = sha256_file(path)
            info["size_bytes"] = path.stat().st_size
        else:
            info["sha256"] = None
            info["missing"] = True
            missing.append(name)
        tools[name] = info
    for name in V4_OPTIONAL_INFO:
        path = repo / V4_DIR_REL / name
        info = {"name": name, "rel": f"{V4_DIR_REL}/{name}", "abs": str(path),
                "required": False}
        if path.is_file():
            info["sha256"] = sha256_file(path)
            info["size_bytes"] = path.stat().st_size
        else:
            info["missing"] = True
        tools[name] = info
    selftest = None
    selftest_path = repo / V4_SELFTEST_SUMMARY_REL
    if selftest_path.is_file():
        selftest = {"rel": V4_SELFTEST_SUMMARY_REL, "sha256": sha256_file(selftest_path),
                    "parsed": try_parse_json(selftest_path.read_bytes())}
    info_all = {"tools": tools, "selftest_summary": selftest,
                "missing_required": missing}
    info_all["stop_reason"] = (f"V4_TOOLS_MISSING: {', '.join(missing)}"
                               if missing else None)
    return info_all


def prior_failures_total(out_dir: Path, current_attempt: int):
    """failures_total continues across attempts: read the newest prior attempt
    summary that parses."""
    best = None
    for path in sorted(out_dir.glob("attempt-*")):
        match = re.fullmatch(r"attempt-(\d+)", path.name)
        if not match or int(match.group(1)) >= current_attempt:
            continue
        summary_path = path / "summary.json"
        if not summary_path.is_file():
            continue
        parsed = try_parse_json(summary_path.read_bytes())
        if isinstance(parsed, dict) and isinstance(parsed.get("failures_total"), int):
            best = (int(match.group(1)), parsed["failures_total"])
    return best[1] if best else 0


def next_attempt_number(out_dir: Path) -> int:
    highest = 0
    for path in out_dir.glob("attempt-*"):
        match = re.fullmatch(r"attempt-(\d+)", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def parse_attempt(value: str) -> int:
    cleaned = value.strip().lower()
    if cleaned.startswith("attempt-"):
        cleaned = cleaned[len("attempt-"):]
    if not re.fullmatch(r"\d+", cleaned):
        raise argparse.ArgumentTypeError(f"bad attempt number: {value!r}")
    return int(cleaned)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agent E2E acceptance runner (Rev21 Vision-reader wave; C1-C5).")
    parser.add_argument("--attempt", default=None,
                        help="attempt number, e.g. 01 (default: next unused)")
    parser.add_argument("--out", default=None,
                        help=f"output base directory (default: {DEFAULT_OUT_DIR})")
    args = parser.parse_args()

    repo = REPO_ROOT
    out_dir = Path(args.out).resolve() if args.out else DEFAULT_OUT_DIR

    try:
        attempt_number = parse_attempt(args.attempt) if args.attempt else \
            next_attempt_number(out_dir)
    except argparse.ArgumentTypeError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    attempt_name = f"attempt-{attempt_number:02d}"
    attempt_dir = out_dir / attempt_name
    if attempt_dir.exists():
        print(f"refusing to overwrite existing attempt directory: {attempt_dir}",
              file=sys.stderr)
        return 4

    os.makedirs(attempt_dir)  # fails if an existing directory appears concurrently
    artifacts = Artifacts(attempt_dir)
    timestamp = now_iso()

    # ---- preflight -------------------------------------------------------
    plan_path = repo / PLAN_REL
    plan_sha = sha256_file(plan_path) if plan_path.is_file() else None
    handoff_path = repo / HANDOFF_REL
    handoff_sha = sha256_file(handoff_path) if handoff_path.is_file() else None
    preflight = {
        "attempt": attempt_name,
        "timestamp_local": timestamp,
        "runner_argv": sys.argv,
        "python": {"executable": sys.executable, "version": sys.version},
        "plan": {"rel": PLAN_REL, "revision_pin": PLAN_REVISION_PIN,
                 "sha256_pin": PLAN_SHA256_PIN, "sha256_observed": plan_sha,
                 "match": plan_sha == PLAN_SHA256_PIN},
        "handoff": {"rel": HANDOFF_REL, "sha256_observed": handoff_sha},
        "env": {"VISION_OCR_BIN": os.environ.get("VISION_OCR_BIN"),
                "CUA_ROUTE_DECISION_present": "CUA_ROUTE_DECISION" in os.environ},
        "inputs_sent": 0, "ui_interaction": "none",
    }
    frames_pf = preflight_frames(repo)
    tools_pf = preflight_v4_tools(repo)
    preflight["frames"] = frames_pf["frames"]
    preflight["v4"] = tools_pf
    artifacts.write_json("raw/preflight.json", preflight)

    prior_total = prior_failures_total(out_dir, attempt_number)
    prior_info = {"prior_failures_total": prior_total,
                  "threshold": MAX_CUMULATIVE_FAILURES,
                  "threshold_already_reached": prior_total >= MAX_CUMULATIVE_FAILURES,
                  "decision_rule": "failures_total continues across attempts; at 5 the "
                                   "loop stops with a recorded stop_reason and no "
                                   "further check is executed"}

    stop_reason = None
    stop_phase = None
    if plan_sha != PLAN_SHA256_PIN:
        stop_reason = (f"PLAN_SHA256_MISMATCH: expected {PLAN_SHA256_PIN}, "
                       f"observed {plan_sha}")
        stop_phase = "preflight_plan_pin"
    elif frames_pf["stop_reason"]:
        stop_reason = frames_pf["stop_reason"]
        stop_phase = "preflight_frames"
    elif tools_pf["stop_reason"]:
        stop_reason = tools_pf["stop_reason"]
        stop_phase = "preflight_v4_tools"
    elif prior_total >= MAX_CUMULATIVE_FAILURES:
        stop_reason = (f"FAILURE_THRESHOLD_REACHED(prior={prior_total}): no check "
                       f"executed in {attempt_name}")
        stop_phase = "bounded_loop_pre_stop"

    check_table = [
        ("C1", check_c1), ("C2", check_c2), ("C3", check_c3),
        ("C4", check_c4), ("C5", check_c5),
    ]
    checks_out = []
    failures_this = 0

    if stop_reason is None:
        ctx = Context(repo, attempt_dir, {name: tools_pf["tools"][name]
                                          for name in tools_pf["tools"]},
                      frames_pf["frames"], artifacts)
        for check_id, function in check_table:
            if stop_reason is not None:
                checks_out.append({"check_id": check_id, "status": "NOT_RUN",
                                   "reason": "bounded loop stopped before this check"})
                continue
            try:
                payload = function(ctx)
            except Exception as exc:
                payload = {"check_id": check_id, "pass": False,
                           "error": f"{type(exc).__name__}: {exc}",
                           "traceback": traceback.format_exc()}
            payload["status"] = "PASS" if payload.get("pass") else "FAIL"
            checks_out.append(payload)
            if not payload.get("pass"):
                failures_this += 1
                if prior_total + failures_this >= MAX_CUMULATIVE_FAILURES:
                    stop_reason = (f"FAILURE_THRESHOLD_REACHED(prior={prior_total}, "
                                   f"this_attempt={failures_this})")
                    stop_phase = stop_phase or "bounded_loop_in_attempt"
            if payload.get("stop_request") and stop_reason is None:
                stop_reason = payload["stop_request"]
                stop_phase = stop_phase or f"check_{check_id}_stop_request"
        helper_info = ctx.direct_helper.info()
        helper_hints = ctx.helper_hints
        helper_summary = None
        if helper_hints and helper_hints[0]["candidate"].get("binary_path"):
            candidate = helper_hints[0]["candidate"]
            helper_summary = {
                "source": "tool_json",
                "json_path": helper_hints[0]["json_path"],
                "binary_path": candidate.get("binary_path"),
                "binary_sha256": candidate.get("binary_sha256"),
                "binary_bytes": candidate.get("binary_bytes"),
                "source_sha256": candidate.get("source_sha256"),
                "resolved_from": candidate.get("resolved_from"),
                "runner_resolved": helper_info,
            }
        else:
            if ctx.direct_helper.method is None:
                ctx.direct_helper.resolve()
            helper_info = ctx.direct_helper.info()
            helper_summary = {
                "source": "runner_resolved",
                "json_path": None,
                "binary_path": helper_info.get("path"),
                "binary_sha256": helper_info.get("sha256"),
                "binary_bytes": helper_info.get("size_bytes"),
                "source_sha256": None,
                "resolved_from": helper_info.get("resolution_method"),
                "runner_resolved": helper_info,
            }
    else:
        for check_id, _ in check_table:
            checks_out.append({"check_id": check_id, "status": "NOT_RUN",
                               "reason": f"stopped before checks: {stop_reason}"})
        helper_info = {"resolution_method": "not_resolved (checks not executed)",
                       "env_VISION_OCR_BIN": os.environ.get("VISION_OCR_BIN"),
                       "path": None, "size_bytes": None, "sha256": None}
        helper_hints = []
        helper_summary = {"source": "not_resolved (checks not executed)",
                          "json_path": None, "binary_path": None,
                          "binary_sha256": None, "binary_bytes": None,
                          "source_sha256": None, "resolved_from": None,
                          "runner_resolved": helper_info}

    failures_total = prior_total + failures_this
    all_pass = (stop_reason is None
                and len(checks_out) == len(check_table)
                and all(check.get("status") == "PASS" for check in checks_out))
    result = "PASS" if all_pass else "FAIL"

    reconcile = artifacts.reconcile_on_disk()

    summary = {
        "schema_version": 1,
        "artifact": "agent-e2e-attempt-summary",
        "wave": "20260917-vision-reader",
        "task_id": TASK_ID,
        "plan_revision": PLAN_REVISION_PIN,
        "runner": {"rel": "evidence/20260916-route/agent-e2e/runner/run_agent_e2e.py",
                   "sha256": sha256_file(Path(__file__).resolve()),
                   "version": RUNNER_VERSION},
        "attempt": attempt_name,
        "timestamp_local": timestamp,
        "runner_argv": sys.argv,
        "python": {"executable": sys.executable,
                   "version": sys.version.split()[0],
                   "full_version": sys.version},
        "result": result,
        "stop_reason": stop_reason,
        "stop_phase": stop_phase,
        "failures_total": failures_total,
        "prior_failures_total": prior_total,
        "attempt_failures": failures_this,
        "bounded_loop": prior_info,
        "inputs_sent": 0,
        "ui_interaction": "none",
        "gui_inputs_sent": 0,
        "screen_captures": 0,
        "model_or_api_calls": 0,
        "formal_data_writes": 0,
        "route_semantics": {
            "cua_route_decision": "not_set",
            "route_closure_decided": False,
            "gui_input_authorized": False,
            "c4_label": "DEMONSTRATION_ONLY",
        },
        "plan": preflight["plan"],
        "handoff": preflight["handoff"],
        "env": preflight["env"],
        "frames": frames_pf["frames"],
        "v4_tools": tools_pf["tools"],
        "v4_selftest_summary": tools_pf["selftest_summary"],
        "helper": helper_summary,
        "helper_from_tool_json": helper_hints,
        "checks": checks_out,
        "frozen_reference": {
            "album_open_verify": FROZEN_V3_ALBUM_OPEN_REL,
            "album_open_verify_sha256_pin": FROZEN_V3_ALBUM_OPEN_SHA256,
        },
        "raw_artifacts": dict(sorted(artifacts.map.items())),
        "raw_reconcile": reconcile,
        "artifacts_dir": str(attempt_dir),
        "acceptance_mode": "INTEGRATION (offline replay over durable frozen frames; "
                           "never reported as live E2E)",
    }
    summary_rel = "summary.json"
    with open(attempt_dir / summary_rel, "wb") as f:
        f.write(json_bytes(summary))

    # SHA256SUMS over raw/ contents (shasum -a 256 format, relative paths)
    raw_dir = attempt_dir / "raw"
    lines = []
    if raw_dir.is_dir():
        for path in sorted(raw_dir.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(attempt_dir))
                lines.append(f"{sha256_file(path)}  {rel}\n")
    with open(attempt_dir / "SHA256SUMS", "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(json.dumps({
        "attempt": attempt_name,
        "result": result,
        "failures_total": failures_total,
        "stop_reason": stop_reason,
        "checks": [{"check_id": check.get("check_id"), "status": check.get("status")}
                   for check in checks_out],
        "summary": str(attempt_dir / summary_rel),
    }, ensure_ascii=False, indent=1))

    if result == "PASS":
        return 0
    if stop_phase in ("bounded_loop_pre_stop", "bounded_loop_in_attempt"):
        return 3
    if stop_phase in ("preflight_plan_pin", "preflight_frames", "preflight_v4_tools"):
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
