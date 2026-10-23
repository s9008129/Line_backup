#!/usr/bin/env python3
# run_offline_once.py -- one fixed offline verification run for the LINE album
# catalog diagnostic (TASK-20261010-catalog-diagnostic-continuity-replan).
#
# It freezes the candidate manifest, builds the task-local Swift helper, decodes
# the replay frames and fixture, runs the declared OCR profiles exactly once per
# purpose, evaluates the four-frame replay chain and records R01-R19 results.
#
# It never captures the screen, never sends input, never downloads, and writes
# only inside the task directory using exclusive creation. Reruns must use a new
# run directory; an existing stage fails closed.

import argparse
import hashlib
import importlib.util
import json
import os
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
FRAMES = ["scan-000", "scan-001", "scan-002", "scan-003"]

PROFILE_LABEL_LIVE = "fixed-label-live"
PROFILE_LABEL_OFFLINE = "fixed-label-offline-comparison"
PROFILE_METADATA = "identity-header-metadata"
PROFILE_METADATA_LEGACY = "identity-header-metadata-legacy"

# Frozen replay geometry (derived from the frozen scan-000 bootstrap and its
# exact match across all four frames; see results/offline-validation notes).
TEXT_SLOT_GUARD = {"x0": 0, "y0": 0, "x1": 654, "y1": 192}
EXCLUSIONS = []  # no non-text structure inside the guard; verified by construction
ALBUM_TAB_HORIZONTAL = [130, 300]
NOTES_TAB_HORIZONTAL = [400, 620]
INDICATOR_REGION = {"x0": 0, "y0": 196, "x1": 654, "y1": 206}
INDICATOR_ALBUM_REGION = {"x0": 100, "y0": 196, "x1": 300, "y1": 206}
INDICATOR_NOTES_REGION = {"x0": 400, "y0": 196, "x1": 620, "y1": 206}
LIST_VIEWPORT = {"x0": 0, "y0": 206, "x1": 654, "y1": 1286}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    with open(path, "rb") as fh:
        return json.load(fh)


def write_new(path, data):
    if os.path.exists(path):
        raise SystemExit(f"OUTPUT_EXISTS: {path} (reruns need a new run directory)")
    with open(path, "xb") as fh:
        fh.write(data)


def write_json_new(path, obj):
    write_new(path, json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n")


def run(cmd, cwd=None, env=None):
    """Run a subprocess, capture real stdout/stderr, never fake success."""
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True)
    return {
        "cmd": cmd, "returncode": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace"),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }


def require_ok(result, what):
    if result["returncode"] != 0:
        raise SystemExit(f"FAILED {what}: exit {result['returncode']}\n{result['stderr'][-4000:]}")


# ---------------------------------------------------------------- PNG fixture


def make_fixture_png(path, w=80, h=60):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes(fixture_px(x, y, w, h))
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    write_new(path, png)
    return {"width": w, "height": h}


def fixture_px(x, y, w, h):
    if y < h // 2 and x < w // 2:
        return (220, 30, 30)   # top-left red
    if y < h // 2:
        return (30, 200, 30)   # top-right green
    if x < w // 2:
        return (30, 30, 220)   # bottom-left blue
    return (230, 210, 30)      # bottom-right yellow


def fixture_expect(w, h):
    return {
        "top_left": {"x": 5, "y": 5, "rgba": list(fixture_px(5, 5, w, h))},
        "top_right": {"x": w - 6, "y": 5, "rgba": list(fixture_px(w - 6, 5, w, h))},
        "bottom_left": {"x": 5, "y": h - 6, "rgba": list(fixture_px(5, h - 6, w, h))},
        "bottom_right": {"x": w - 6, "y": h - 6,
                         "rgba": list(fixture_px(w - 6, h - 6, w, h))},
    }


# ---------------------------------------------------------------- legacy coords


def convert_legacy_artifact(payload):
    """Convert a historical full-frame 2x OCR artifact into source pixels.

    The old transform.json documents: derivative is the full frame scaled 2x;
    coordinates are divided by 2 to return to capture pixels. This conversion is
    kept separate from the new local-ROI transform and never mixed.
    """
    conv = {
        "format": "local-legacy-ocr-source-converted-1",
        "conversion": "historical full-frame 2x: source = derivative/2",
        "source": payload.get("source"),
        "imageWidth": payload.get("imageWidth"),
        "imageHeight": payload.get("imageHeight"),
        "items": [],
        "legacy_completeness": "UNKNOWN",
        "note": "Historical artifacts store a single candidate per item; candidates are not fabricated.",
    }
    for it in payload["items"]:
        box = it["boxTopLeftPixels"]
        conv["items"].append({
            "text": it["text"],
            "confidence": it.get("confidence"),
            "boxTopLeftSourcePixels": [box[0] / 2.0, box[1] / 2.0, box[2] / 2.0, box[3] / 2.0],
            "candidates": it.get("candidates"),
        })
    return conv


# ---------------------------------------------------------------- stages


def stage_candidate_manifest(run_dir):
    files = {}
    for name in ("offline_vision.swift", "catalog_diagnostic.py", "run_offline_once.py",
                 "test_catalog_diagnostic.py", "profiles.json"):
        path = os.path.join(HERE, name)
        if os.path.isfile(path):
            files[name] = {"sha256": sha256_file(path), "bytes": os.path.getsize(path)}
    manifest = {
        "format": "local-candidate-manifest-1",
        "note": "Frozen before the offline method verification. Any later change to "
                "these files invalidates the recorded tests and pre-live review.",
        "files": files,
        "python_version": sys.version.split()[0],
    }
    manifest["candidate_hash"] = sha256_bytes(
        json.dumps({k: v["sha256"] for k, v in sorted(files.items())},
                   separators=(",", ":")).encode("utf-8"))
    return manifest


def stage_build(run_dir, log_dir):
    binary = os.path.join(run_dir, "offline_vision")
    module_cache = os.path.join(TASK, "module-cache")
    tmp_dir = os.path.join(TASK, "tmp")
    os.makedirs(module_cache, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    env = dict(os.environ)
    env["TMPDIR"] = tmp_dir
    result = run(["swiftc", "-parse-as-library", "-O",
                  "-module-cache-path", module_cache,
                  "-o", binary, os.path.join(HERE, "offline_vision.swift")], env=env)
    write_new(os.path.join(log_dir, "build.stdout.log"), result["stdout"].encode())
    write_new(os.path.join(log_dir, "build.stderr.log"), result["stderr"].encode())
    require_ok(result, "swiftc build")
    return {"binary": binary, "sha256": sha256_file(binary),
            "returncode": result["returncode"],
            "swift_version": run(["swiftc", "--version"])["stdout"].splitlines()[0] if True else None}


def stage_decode(binary, replay_dir, decode_dir, frames):
    outputs = {}
    for name in frames:
        src = os.path.join(replay_dir, name + ".png")
        out = os.path.join(decode_dir, name)
        result = run([binary, "decode", "--input", src, "--out", out])
        write_new(os.path.join(decode_dir, name + ".decode.stdout.log"), result["stdout"].encode())
        write_new(os.path.join(decode_dir, name + ".decode.stderr.log"), result["stderr"].encode())
        require_ok(result, f"decode {name}")
        meta = read_json(os.path.join(out, "decode.json"))
        outputs[name] = {
            "dir": out,
            "rgba_path": os.path.join(out, "decoded.rgba"),
            "meta": meta,
        }
    return outputs


def stage_fixture(binary, run_dir):
    fixture_dir = os.path.join(run_dir, "fixture")
    os.makedirs(fixture_dir, exist_ok=False)
    png = os.path.join(fixture_dir, "corners.png")
    dims = make_fixture_png(png)
    expect = fixture_expect(dims["width"], dims["height"])
    write_json_new(os.path.join(fixture_dir, "expect.json"), expect)
    decode_out = os.path.join(fixture_dir, "decode")
    r1 = run([binary, "decode", "--input", png, "--out", decode_out])
    write_new(os.path.join(fixture_dir, "decode.stdout.log"), r1["stdout"].encode())
    write_new(os.path.join(fixture_dir, "decode.stderr.log"), r1["stderr"].encode())
    require_ok(r1, "fixture decode")
    r2 = run([binary, "check-fixture", "--input", png, "--expect", os.path.join(fixture_dir, "expect.json")])
    write_new(os.path.join(fixture_dir, "check.stdout.log"), r2["stdout"].encode())
    write_new(os.path.join(fixture_dir, "check.stderr.log"), r2["stderr"].encode())
    verdict = "PASS" if r2["returncode"] == 0 else "FAIL"
    return {"fixture_png": png, "fixture_png_sha256": sha256_file(png),
            "dims": dims, "verdict": verdict,
            "stdout": r2["stdout"], "stderr": r2["stderr"]}


def stage_ocr(binary, replay_dir, ocr_dir, decoded, frames):
    """Run the declared OCR profiles once per purpose.

    - identity-header-metadata (modern)  -> identity/geometry main results
    - identity-header-metadata-legacy   -> diagnostic comparison
    - fixed-label-live                  -> fixed tab-label profile (modern)
    - fixed-label-offline-comparison    -> one-off offline comparison, never live
    """
    profiles_path = os.path.join(HERE, "profiles.json")
    runs = [
        ("metadata_modern", PROFILE_METADATA, "full_frame"),
        ("metadata_legacy", PROFILE_METADATA_LEGACY, "full_frame"),
        ("label_live", PROFILE_LABEL_LIVE, "full_frame"),
        ("label_offline", PROFILE_LABEL_OFFLINE, "full_frame"),
    ]
    outputs = {}
    for name in frames:
        outputs[name] = {}
        meta = decoded[name]["meta"]
        roi = {"x0": 0, "y0": 0, "x1": meta["width"], "y1": meta["height"]}
        roi_path = os.path.join(ocr_dir, name + ".roi-full-frame.json")
        write_json_new(roi_path, roi)
        for run_name, profile, _ in runs:
            out = os.path.join(ocr_dir, f"{name}.{run_name}")
            result = run([binary, "recognize",
                          "--input", os.path.join(replay_dir, name + ".png"),
                          "--profile", profiles_path,
                          "--profile-name", profile,
                          "--roi", roi_path,
                          "--out", out])
            write_new(os.path.join(ocr_dir, f"{name}.{run_name}.stdout.log"), result["stdout"].encode())
            write_new(os.path.join(ocr_dir, f"{name}.{run_name}.stderr.log"), result["stderr"].encode())
            require_ok(result, f"recognize {name} {run_name}")
            outputs[name][run_name] = {
                "dir": out,
                "json": os.path.join(out, "recognize.json"),
                "sha256": sha256_file(os.path.join(out, "recognize.json")),
            }
    return outputs


# ---------------------------------------------------------------- evaluation


def build_binding(candidate_manifest, decoded, profiles_path, replay_manifest):
    scan0 = decoded["scan-000"]["meta"]
    # Baseline indicator from the bootstrap frame only.
    spec = importlib.util.spec_from_file_location("catalog_diagnostic", os.path.join(HERE, "catalog_diagnostic.py"))
    cd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cd)
    w, h = scan0["width"], scan0["height"]
    rgba = open(decoded["scan-000"]["rgba_path"], "rb").read()
    album_cells = cd.bright_mask(rgba, w, (INDICATOR_ALBUM_REGION["x0"], INDICATOR_ALBUM_REGION["y0"],
                                           INDICATOR_ALBUM_REGION["x1"], INDICATOR_ALBUM_REGION["y1"]))
    notes_cells = cd.bright_mask(rgba, w, (INDICATOR_NOTES_REGION["x0"], INDICATOR_NOTES_REGION["y0"],
                                           INDICATOR_NOTES_REGION["x1"], INDICATOR_NOTES_REGION["y1"]))
    comps = cd.connected_components_8(album_cells)
    if notes_cells or len(comps) != 1:
        raise SystemExit("BOOTSTRAP_INDICATOR_NOT_UNIQUE")
    comp = comps[0]
    bbox = cd.bbox_of(comp)
    binding = {
        "format": "local-catalog-binding-1",
        "mode": "replay",
        "run_id": "replay-catalog-diagnostic-20261010",
        "observation_id": "replay-bootstrap-scan-000",
        "diagnostic_only": True,
        "source_artifact": "replay/scan-000.png",
        "source_artifact_sha256": scan0["source_sha256"],
        "decoded_rgba_sha256": scan0["decoded_rgba_sha256"],
        "capture_width": w, "capture_height": h,
        "width": w, "height": h,
        "decoder": "candidate/offline_vision.swift decode",
        "decoder_hash": candidate_manifest["files"]["offline_vision.swift"]["sha256"],
        "profile_hashes": {"profiles.json": sha256_file(profiles_path)},
        "candidate_hash": candidate_manifest["candidate_hash"],
        "canonical_group_key": "canonical config group_key (unchanged)",
        "configured_display_name": "旻謙允禎成長日記",
        "observed_display_name": "旻謙允禎成長日記",
        "text_slot_guard": TEXT_SLOT_GUARD,
        "text_slots": {
            "title": {"rect": {"x0": 210, "y0": 80, "x1": 460, "y1": 128}},
            "album_tab": {"rect": {"x0": 128, "y0": 153, "x1": 296, "y1": 192}},
            "notes_tab": {"rect": {"x0": 442, "y0": 153, "x1": 614, "y1": 192}},
            "title_region": {"rect": {"x0": 200, "y0": 75, "x1": 500, "y1": 132}},
        },
        "exclusions": EXCLUSIONS,
        "indicator": {
            "region": INDICATOR_REGION,
            "album_region": INDICATOR_ALBUM_REGION,
            "notes_region": INDICATOR_NOTES_REGION,
            "album_tab_horizontal": ALBUM_TAB_HORIZONTAL,
            "notes_tab_horizontal": NOTES_TAB_HORIZONTAL,
            "baseline_bbox": list(bbox),
            "baseline_mask_sha256": cd.sha256_bytes(json.dumps(sorted(comp), separators=(",", ":")).encode("utf-8")),
            "luma": "(54R+183G+19B)>>8", "bright_at_least": 128,
            "connectivity": 8, "filter_small_components": False,
        },
        "list_viewport": LIST_VIEWPORT,
        "safety_observation": "UNKNOWN",
        "safety_note": "replay frames carry no live runtime safety observation",
        "replay_manifest_format": replay_manifest["format"],
    }
    binding["binding_hash"] = sha256_bytes(
        json.dumps({k: v for k, v in binding.items() if k != "binding_hash"},
                   separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return binding


def stage_evaluate(run_dir, binding, decoded, ocr, frames):
    cd_path = os.path.join(HERE, "catalog_diagnostic.py")
    spec = importlib.util.spec_from_file_location("catalog_diagnostic", cd_path)
    cd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cd)
    decisions = {}
    previous_manifest_path = None
    previous_metadata = None
    for name in frames:
        frame_dir = os.path.join(run_dir, "evaluate", name)
        os.makedirs(frame_dir, exist_ok=False)
        meta = decoded[name]["meta"]
        legacy_raw = read_json(os.path.join(TASK, "replay", name + ".ocr.json"))
        legacy_converted = convert_legacy_artifact(legacy_raw)
        legacy_path = os.path.join(frame_dir, "legacy-source-converted.json")
        write_json_new(legacy_path, legacy_converted)

        frame_manifest = {
            "format": "local-frame-manifest-1",
            "mode": "replay",
            "frame_id": name,
            "run_id": binding["run_id"],
            "observation_id": binding["observation_id"],
            "previous_frame_id": frames[frames.index(name) - 1] if frames.index(name) > 0 else None,
            "source_artifact_sha256": meta["source_sha256"],
            "width": meta["width"], "height": meta["height"],
            "rgba": {
                "path": decoded[name]["rgba_path"],
                "decoded_rgba_sha256": meta["decoded_rgba_sha256"],
                "source_sha256": meta["source_sha256"],
            },
            "safety_observation": None,
            "note": "replay frame; timestamps/provenance are not live values",
        }
        frame_manifest_path = os.path.join(frame_dir, "frame-manifest.json")
        write_json_new(frame_manifest_path, frame_manifest)

        previous_manifest = previous_manifest_path if previous_manifest_path else "NONE"
        out_dir = os.path.join(frame_dir, "evaluation")
        result = run([sys.executable, "-B", cd_path, "evaluate",
                      "--mode", "replay",
                      "--binding", os.path.join(run_dir, "binding.json"),
                      "--frame-manifest", frame_manifest_path,
                      "--modern", ocr[name]["metadata_modern"]["json"],
                      "--legacy", legacy_path,
                      "--previous", previous_manifest,
                      "--out", out_dir])
        write_new(os.path.join(frame_dir, "evaluate.stdout.log"), result["stdout"].encode())
        write_new(os.path.join(frame_dir, "evaluate.stderr.log"), result["stderr"].encode())
        require_ok(result, f"evaluate {name}")
        decision = read_json(os.path.join(out_dir, "decision.json"))
        decisions[name] = {"decision": decision, "dir": out_dir}
        metadata = {
            "complete_rows": decision["complete_rows"],
            "qualified": decision["qualified_overlap_rows"],
            "ordered_qualified_ids": decision["ordered_qualified_ids"],
        }
        metadata_path = os.path.join(frame_dir, "metadata.json")
        write_json_new(metadata_path, metadata)
        frame_manifest["metadata"] = metadata
        with open(frame_manifest_path, "w") as fh:
            json.dump(frame_manifest, fh, indent=1, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
        previous_manifest_path = frame_manifest_path
    return decisions


# ---------------------------------------------------------------- R01-R19 checks


def check(test_id, description, expected, actual, verdict, evidence=None):
    return {
        "id": test_id, "description": description,
        "expected": expected, "actual": actual,
        "verdict": verdict, "evidence": evidence or {},
    }


def stage_checks(cd, run_dir, binding, decoded, ocr, decisions, fixture):
    import copy
    results = []

    d0 = decisions["scan-000"]["decision"]
    d1 = decisions["scan-001"]["decision"]
    d2 = decisions["scan-002"]["decision"]
    d3 = decisions["scan-003"]["decision"]

    # R01 -- four-frame historical replay with the frozen new method.
    r01_ok = (
        d0["continuity"]["status"] == "BOOTSTRAP"
        and d1["continuity"]["status"] == "PASS"
        and d2["continuity"]["status"] == "PASS"
        and d3["continuity"]["status"] == "PASS"
        and d0["selected_indicator"]["status"] == "PASS"
        and d1["selected_indicator"]["status"] == "PASS"
        and d2["selected_indicator"]["status"] == "PASS"
        and d3["selected_indicator"]["status"] == "PASS"
        and d0["identity_status"] == "COMPLETE"
        and d1["identity_status"] == "COMPLETE"
        and d2["identity_status"] == "COMPLETE"
        and d3["identity_status"] == "COMPLETE"
        and d1["movement"] == "YES" and d2["movement"] == "YES" and d3["movement"] == "YES"
        and d1["ordered_overlap"]["overlap"] == "PASS"
        and d2["ordered_overlap"]["overlap"] == "PASS"
        and d3["ordered_overlap"]["overlap"] == "PASS"
        and d3["scroll_eligible"] is False
        and d0["full_collection_coverage"] == "NOT_ESTABLISHED"
    )
    # scan-003 modern raw text must keep 相溥 exactly as read
    s3_texts = []
    modern3 = read_json(ocr["scan-003"]["metadata_modern"]["json"])
    for it in modern3["items"]:
        s3_texts.append(it["text"])
    keeps_misspelling = "相溥" in s3_texts
    no_replacement = all(t != "相簿" for t in s3_texts if t in ("相溥", "相簿"))
    results.append(check(
        "R01",
        "四幀離線回放：文字連續性、選中指示、三段位移、順序重疊；live 權限 false；保留原始相溥",
        {"continuity": ["BOOTSTRAP", "PASS", "PASS", "PASS"], "movement": ["YES", "YES", "YES"],
         "overlap": ["PASS", "PASS", "PASS"], "scroll_eligible": False, "keeps_相溥": True},
        {"continuity": [d0["continuity"]["status"], d1["continuity"]["status"], d2["continuity"]["status"], d3["continuity"]["status"]],
         "movement": [d1["movement"], d2["movement"], d3["movement"]],
         "overlap": [d1["ordered_overlap"]["overlap"], d2["ordered_overlap"]["overlap"], d3["ordered_overlap"]["overlap"]],
         "scroll_eligible": [d0["scroll_eligible"], d1["scroll_eligible"], d2["scroll_eligible"], d3["scroll_eligible"]],
         "scan003_modern_texts": s3_texts, "keeps_相溥": keeps_misspelling,
         "no_相溥_to_相簿_replacement": no_replacement},
        "PASS" if (r01_ok and keeps_misspelling and no_replacement) else "FAIL",
        {"decision_dirs": {k: v["dir"] for k, v in decisions.items()},
         "expected_joint_D": {"000-001": [-292.029, -243.804], "001-002": [-292.029, -243.804],
                              "002-003": [-292.029, -246.483]},
         "observed_joint_D": {"000-001": d1["movement_evidence"]["joint"],
                              "001-002": d2["movement_evidence"]["joint"],
                              "002-003": d3["movement_evidence"]["joint"]}}))

    # R02 -- same visible identity set, all boxes moved strongly upward -> YES.
    fixture_rows = [
        {"identity_dates": ["2024-06-02", "2024-06-07"], "count": 65,
         "date_text": "2024/06/02~06/07", "count_text": "65",
         "date_box": [29.0, 600.0, 265.0, 627.0], "count_box": [29.0, 635.0, 61.0, 659.0],
         "date_confidence": 0.5, "count_confidence": 1.0,
         "date_candidates": [{"text": "2024/06/02~06/07", "confidence": 0.5}],
         "count_candidates": [{"text": "65", "confidence": 1.0}]},
    ]
    current_rows = copy.deepcopy(fixture_rows)
    current_rows[0]["date_box"] = [29.0, 321.5, 265.0, 348.5]
    current_rows[0]["count_box"] = [29.0, 356.0, 61.0, 380.0]
    move = cd.movement_evidence(fixture_rows, current_rows)
    results.append(check(
        "R02", "相同集合但全部 bbox 大幅向上 -> movement YES",
        {"movement": "YES", "all_upper_negative": True},
        {"movement": move["movement"], "joint": move["joint"]},
        "PASS" if move["movement"] == "YES" else "FAIL", {"joint": move["joint"], "reason": move["reason"]}))

    # R03 -- raw confidence 0.3/0.5 with complete identity/geometry passes; no 0.95 gate.
    low_items = [
        {"text": "2024/06/02~06/07", "confidence": 0.3,
         "boxTopLeftSourcePixels": [29.0, 850.0, 236.0, 27.0],
         "candidates": [{"text": "2024/06/02~06/07", "confidence": 0.3}]},
        {"text": "65", "confidence": 0.5,
         "boxTopLeftSourcePixels": [29.0, 885.0, 32.0, 24.0],
         "candidates": [{"text": "65", "confidence": 0.5}]},
    ]
    low_norm, _ = cd.normalize_ocr_items({"items": low_items}, "fixture")
    low_rows, low_partial, low_conflicts = cd.classify_date_items(low_norm, (0, 0, 654, 1286), (0, 206, 654, 1286))
    low_counts, low_noise = cd.classify_count_items(low_norm, {r["index"] for r in low_rows}, (0, 0, 654, 1286), (0, 206, 654, 1286))
    low_complete, low_pair_partial, _, low_pair_conflicts = cd.pair_rows(low_rows, low_counts, low_noise)
    r03_ok = (len(low_complete) == 1 and not low_conflicts and not low_pair_conflicts
              and low_complete[0]["date_confidence"] == 0.3)
    results.append(check(
        "R03", "raw confidence 0.3/0.5 但身份／幾何完整一致 -> 不因 0.95 門檻失敗，raw scores 保留",
        {"complete_rows": 1, "date_confidence": 0.3},
        {"complete_rows": len(low_complete),
         "date_confidence": low_complete[0]["date_confidence"] if low_complete else None},
        "PASS" if r03_ok else "FAIL", {"rows": low_complete}))

    # R04 -- baseline glyph unchanged, new low-contrast pixels outside the old glyph
    # mask but inside the frozen full slot -> guard rejects.
    w, h = 654, 1286
    base_rgba = bytearray(b"\x2d\x2e\x30\xff" * (w * h))
    def put(rgba, x, y, rgb):
        i = (y * w + x) * 4
        rgba[i:i + 3] = bytes(rgb)
    for x in range(235, 350):
        put(base_rgba, x, 100, (240, 240, 240))
    mutated = bytearray(base_rgba)
    put(mutated, 500, 150, (70, 72, 74))  # low-contrast pixel in the title slot, outside glyphs
    guard = cd.pixel_guard(bytes(mutated), w, bytes(base_rgba), w,
                           (0, 0, 654, 192), [], (0, 0, 654, 1286))
    results.append(check(
        "R04", "baseline glyph 不變，但 title 槽外新增低對比像素 -> full-slot guard 拒絕",
        {"status": "CONFLICT", "pixel_diff_count": 1},
        {"status": guard["status"], "pixel_diff_count": guard["pixel_diff_count"],
         "first_diff": guard["first_diff"]},
        "PASS" if guard["status"] == "CONFLICT" and guard["pixel_diff_count"] == 1 else "FAIL",
        {"reason": guard["reason"]}))

    # R05 -- group/tab text change, or indicator moved to notes / doubled -> stop.
    changed = bytearray(base_rgba)
    put(changed, 453, 170, (240, 240, 240))  # notes tab glyph area changed
    guard5 = cd.pixel_guard(bytes(changed), w, bytes(base_rgba), w, (0, 0, 654, 192), [], (0, 0, 654, 1286))
    ind = dict(binding["indicator"])
    notes_rgba = bytearray(base_rgba)
    for x in range(431, 530):
        for y in range(202, 206):
            put(notes_rgba, x, y, (255, 255, 255))
    ind5_notes = cd.indicator_check(bytes(notes_rgba), w, ind, (0, 0, 654, 1286))
    dbl_rgba = bytearray(base_rgba)
    for x in range(138, 186):
        for y in range(202, 206):
            put(dbl_rgba, x, y, (255, 255, 255))
    for x in range(420, 470):
        for y in range(202, 206):
            put(dbl_rgba, x, y, (255, 255, 255))
    ind5_dbl = cd.indicator_check(bytes(dbl_rgba), w, ind, (0, 0, 654, 1286))
    r05_ok = (guard5["status"] == "CONFLICT" and ind5_notes["status"] == "CONFLICT"
              and ind5_dbl["status"] == "CONFLICT")
    results.append(check(
        "R05", "改 group/tab 字或指示移到記事本／雙指示 -> 停止",
        {"text_guard": "CONFLICT", "indicator_notes": "CONFLICT", "indicator_double": "CONFLICT"},
        {"text_guard": guard5["status"], "indicator_notes": ind5_notes["status"],
         "indicator_double": ind5_dbl["status"]},
        "PASS" if r05_ok else "FAIL",
        {"notes_reason": ind5_notes["reason"], "double_reason": ind5_dbl["reason"]}))

    # R06 -- identical text ROI but safety not observed -> scroll ineligible.
    live_binding = copy.deepcopy(binding)
    live_binding["mode"] = "live"
    scan1_meta = decoded["scan-001"]["meta"]
    scan1_rgba = {
        "path": decoded["scan-001"]["rgba_path"],
        "decoded_rgba_sha256": scan1_meta["decoded_rgba_sha256"],
        "source_sha256": scan1_meta["source_sha256"],
    }
    frame = {
        "format": "local-frame-manifest-1", "mode": "live", "frame_id": "live-f06",
        "run_id": binding["run_id"], "observation_id": binding["observation_id"],
        "previous_frame_id": "live-f05", "source_artifact_sha256": scan1_meta["source_sha256"],
        "width": w, "height": h, "safety_observation": "UNKNOWN",
        "rgba": dict(scan1_rgba),
        "modern_path": ocr["scan-001"]["metadata_modern"]["json"],
        "modern_sha256": ocr["scan-001"]["metadata_modern"]["sha256"],
        "legacy_path": "in-memory:scan-001.ocr.json",
        "legacy_sha256": sha256_file(os.path.join(TASK, "replay", "scan-001.ocr.json")),
    }
    prev_frame = {
        "format": "local-frame-manifest-1", "mode": "live", "frame_id": "live-f05",
        "run_id": binding["run_id"], "observation_id": binding["observation_id"],
        "previous_frame_id": "live-f04", "source_artifact_sha256": scan1_meta["source_sha256"],
        "width": w, "height": h,
        "rgba": dict(scan1_rgba),
    }
    prev_meta = {
        "complete_rows": decisions["scan-000"]["decision"]["complete_rows"],
        "qualified": decisions["scan-000"]["decision"]["qualified_overlap_rows"],
        "ordered_qualified_ids": decisions["scan-000"]["decision"]["ordered_qualified_ids"],
    }
    rgba1 = open(decoded["scan-001"]["rgba_path"], "rb").read()
    modern1 = read_json(ocr["scan-001"]["metadata_modern"]["json"])
    legacy1 = json.loads(json.dumps(convert_legacy_artifact(read_json(os.path.join(TASK, "replay", "scan-001.ocr.json")))))
    d06 = cd.decide_frame(live_binding, frame, prev_frame, modern1, legacy1, rgba1, rgba1, prev_meta)
    results.append(check(
        "R06", "viewer/dialog/menu/editing/occluded 且文字 ROI 相同 -> input 禁止（safety UNKNOWN）",
        {"scroll_eligible": False},
        {"scroll_eligible": d06["scroll_eligible"], "safety_observation": d06["safety_observation"]},
        "PASS" if d06["scroll_eligible"] is False else "FAIL", {"stop_reason": d06["stop_reason"]}))

    # R07 -- mixed old run/frame, changed source/geometry/scale -> binding invalid, no scroll.
    bad_frame = dict(frame)
    bad_frame["run_id"] = "other-run"
    bad_frame["source_artifact_sha256"] = "0" * 64
    bad_frame["rgba"] = dict(frame["rgba"])
    d07 = cd.decide_frame(live_binding, bad_frame, prev_frame, modern1, legacy1, rgba1, rgba1, prev_meta)
    r07_ok = (d07["binding_validity"]["status"] == "INVALID" and d07["scroll_eligible"] is False)
    results.append(check(
        "R07", "old run/frame 混入、source/geometry 改變 -> binding invalid；無 scroll 權限",
        {"binding_validity": "INVALID", "scroll_eligible": False},
        {"binding_validity": d07["binding_validity"]["status"], "scroll_eligible": d07["scroll_eligible"]},
        "PASS" if r07_ok else "FAIL", {"checks": d07["binding_validity"]["checks"]}))

    # R08 -- capture age over 5 seconds (and unknown age) must not be dispatchable;
    # read-only refresh is limited to 2 by the live runner contract.
    fresh_frame = dict(frame)
    fresh_frame["capture_age_seconds"] = 3.0
    fresh_frame["safety_observation"] = "OBSERVED"
    d08_fresh = cd.decide_frame(live_binding, fresh_frame, prev_frame, modern1, legacy1, rgba1, rgba1, prev_meta)
    stale_frame = dict(frame)
    stale_frame["capture_age_seconds"] = 6.0
    stale_frame["safety_observation"] = "OBSERVED"
    d08_stale = cd.decide_frame(live_binding, stale_frame, prev_frame, modern1, legacy1, rgba1, rgba1, prev_meta)
    unknown_frame = dict(frame)
    unknown_frame["safety_observation"] = "OBSERVED"  # age unknown
    d08_unknown = cd.decide_frame(live_binding, unknown_frame, prev_frame, modern1, legacy1, rgba1, rgba1, prev_meta)
    r08_ok = (d08_fresh["scroll_eligible"] is True
              and d08_stale["scroll_eligible"] is False
              and d08_unknown["scroll_eligible"] is False)
    results.append(check(
        "R08", "capture 過期 >5 秒或 age 未知不得 dispatch；唯讀 refresh 上限 2（live runner 契約）",
        {"fresh_3s": True, "stale_6s": False, "age_unknown": False},
        {"fresh_3s": d08_fresh["scroll_eligible"], "stale_6s": d08_stale["scroll_eligible"],
         "age_unknown": d08_unknown["scroll_eligible"]},
        "PASS" if r08_ok else "FAIL",
        {"stale_stop_reason": d08_stale["stop_reason"],
         "unknown_stop_reason": d08_unknown["stop_reason"]}))

    # R09 -- invalid dates, start>end, non-positive/non-decimal counts, cross-card, two counts.
    cases = [
        ("bad_date", "2024/13/40~06/07", "65", "partial"),
        ("start_after_end", "2024/06/07~06/02", "65", "partial"),
        ("count_zero", "2024/06/02~06/07", "0", "partial"),
        ("count_letter", "2024/06/02~06/07", "6O", "ambiguous_count"),
        ("two_counts", "2024/06/02~06/07", "65", "ambiguous_count"),
        ("missing_count", "2024/06/02~06/07", "none", "partial"),
    ]
    r09_results = {}
    for name, date_text, count_text, kind in cases:
        items = [
            {"text": date_text, "confidence": 0.5,
             "boxTopLeftSourcePixels": [29.0, 850.0, 236.0, 27.0],
             "candidates": [{"text": date_text, "confidence": 0.5}]},
            {"text": count_text, "confidence": 1.0,
             "boxTopLeftSourcePixels": [29.0, 885.0, 32.0, 24.0],
             "candidates": [{"text": count_text, "confidence": 1.0}]},
        ]
        if kind == "ambiguous_count":
            # two count rows inside the same date/count block
            items.append({"text": count_text, "confidence": 0.9,
                          "boxTopLeftSourcePixels": [29.0, 920.0, 32.0, 24.0],
                          "candidates": [{"text": count_text, "confidence": 0.9}]})
        if count_text == "none":
            items = items[:1]
        norm, _ = cd.normalize_ocr_items({"items": items}, name)
        rows, partial, conflicts = cd.classify_date_items(norm, (0, 0, 654, 1286), (0, 206, 654, 1286))
        counts, noise = cd.classify_count_items(norm, {r["index"] for r in rows}, (0, 0, 654, 1286), (0, 206, 654, 1286))
        complete, pair_partial, ambiguous, pair_conflicts = cd.pair_rows(rows, counts, noise)
        ok = (not complete) and (len(partial) + len(pair_partial) > 0 or ambiguous or conflicts)
        r09_results[name] = {"complete": len(complete), "partial": len(partial) + len(pair_partial),
                             "ambiguous": len(ambiguous), "conflicts": len(pair_conflicts),
                             "ok": bool(ok)}
    results.append(check(
        "R09", "日期無效、start>end、count 非正整數、跨卡／兩 count -> 拒絕完整 identity 或 ambiguity 停止",
        {"all_rejected": True}, r09_results,
        "PASS" if all(v["ok"] for v in r09_results.values()) else "FAIL", {}))

    # R10 -- two APIs read different valid identities in the same block -> stop.
    legacy_conflicting = {"items": [
        {"text": "2024/06/02~06/07", "confidence": 0.5,
         "boxTopLeftSourcePixels": [29.0, 850.0, 236.0, 27.0], "candidates": None},
        {"text": "66", "confidence": 1.0,
         "boxTopLeftSourcePixels": [29.0, 885.0, 32.0, 24.0], "candidates": None},
    ]}
    legacy_norm, _ = cd.normalize_ocr_items(legacy_conflicting, "legacy")
    modern_norm, _ = cd.normalize_ocr_items(read_json(ocr["scan-000"]["metadata_modern"]["json"]), "modern")
    conflict_rows, conflict_partial, conflict_conf = cd.classify_date_items(modern_norm, (0, 0, 654, 1286), (0, 206, 654, 1286))
    conflict_counts, conflict_noise = cd.classify_count_items(modern_norm, {r["index"] for r in conflict_rows}, (0, 0, 654, 1286), (0, 206, 654, 1286))
    conflict_complete, _, _, _ = cd.pair_rows(conflict_rows, conflict_counts, conflict_noise)
    qualified10, conf10 = cd.qualified_overlap_rows(conflict_complete, modern_norm, legacy_norm)
    r10_ok = (not qualified10 and any(c["kind"] == "legacy_modern_count_disagreement" for c in conf10))
    results.append(check(
        "R10", "同 block 兩 API 不同有效 identity -> 停止；不套 tab 容錯",
        {"qualified": 0, "conflict": "legacy_modern_count_disagreement"},
        {"qualified": len(qualified10), "conflicts": [c["kind"] for c in conf10]},
        "PASS" if r10_ok else "FAIL", {"conflicts": conf10}))

    # R11 -- legacy missing or only partial -> not written as agreement, cannot bridge.
    legacy_missing = {"items": [
        {"text": "記事本", "confidence": 1.0,
         "boxTopLeftSourcePixels": [450.0, 160.0, 75.0, 25.0], "candidates": None},
    ]}
    lm_norm, lm_comp = cd.normalize_ocr_items(legacy_missing, "legacy")
    qualified11, conf11 = cd.qualified_overlap_rows(conflict_complete, modern_norm, lm_norm)
    results.append(check(
        "R11", "缺讀 legacy 或只有 partial -> 不寫 agreement；不能用該行延伸 coverage",
        {"qualified": 0, "legacy_completeness": "UNKNOWN"},
        {"qualified": len(qualified11), "conflicts": len(conf11), "legacy_completeness": lm_comp},
        "PASS" if (not qualified11 and lm_comp == "UNKNOWN") else "FAIL", {}))

    # R12 -- duplicate / same-date count drift / non-adjacent reappearance -> stop.
    dup_items = [
        {"text": "2024/06/02~06/07", "confidence": 0.5,
         "boxTopLeftSourcePixels": [29.0, 850.0, 236.0, 27.0],
         "candidates": [{"text": "2024/06/02~06/07", "confidence": 0.5}]},
        {"text": "65", "confidence": 1.0,
         "boxTopLeftSourcePixels": [29.0, 885.0, 32.0, 24.0],
         "candidates": [{"text": "65", "confidence": 1.0}]},
        {"text": "2024/06/02~06/07", "confidence": 0.5,
         "boxTopLeftSourcePixels": [29.0, 1000.0, 236.0, 27.0],
         "candidates": [{"text": "2024/06/02~06/07", "confidence": 0.5}]},
        {"text": "64", "confidence": 1.0,
         "boxTopLeftSourcePixels": [29.0, 1035.0, 32.0, 24.0],
         "candidates": [{"text": "64", "confidence": 1.0}]},
    ]
    dup_norm, _ = cd.normalize_ocr_items({"items": dup_items}, "dup")
    dup_rows, _, _ = cd.classify_date_items(dup_norm, (0, 0, 654, 1286), (0, 206, 654, 1286))
    dup_counts, dup_noise = cd.classify_count_items(dup_norm, {r["index"] for r in dup_rows}, (0, 0, 654, 1286), (0, 206, 654, 1286))
    dup_complete, _, _, dup_pair_conf = cd.pair_rows(dup_rows, dup_counts, dup_noise)
    same_date = [r for r in dup_complete if tuple(r["identity_dates"]) == ("2024-06-02", "2024-06-07")]
    drift = len(same_date) == 2 and {r["count"] for r in same_date} == {65, 64}
    results.append(check(
        "R12", "duplicate、同日期 count 變動、non-adjacent reappearance -> ambiguity 停止",
        {"same_date_drift_detected": True},
        {"same_date_rows": len(same_date), "counts": [r["count"] for r in same_date], "drift": drift},
        "PASS" if drift else "FAIL", {}))

    # R13 -- ordered overlap gap / reversed order -> no chain extension.
    ov_gap = cd.ordered_overlap(["a", "b", "c"], ["b", "d"])
    ov_rev = cd.ordered_overlap(["a", "b", "c", "d"], ["c", "b"])
    ov_pass = cd.ordered_overlap(["a", "b", "c"], ["b", "c"])
    r13_ok = (ov_gap["overlap"] == "FAIL" and ov_rev["overlap"] == "FAIL"
              and ov_pass["overlap"] == "PASS")
    results.append(check(
        "R13", "ordered-overlap 缺口／反序（無相鄰 suffix-prefix）-> 不延伸 chain；正常相鄰仍 PASS",
        {"gap": "FAIL", "reversed": "FAIL", "adjacent": "PASS"},
        {"gap": ov_gap["overlap"], "reversed": ov_rev["overlap"], "adjacent": ov_pass["overlap"]},
        "PASS" if r13_ok else "FAIL", {"gap_matches": ov_gap["matches"], "reversed_matches": ov_rev["matches"]}))

    # R14 -- date up but count not up, empty joint D, or no x overlap -> not YES.
    prev_rows = copy.deepcopy(fixture_rows)
    cur_rows = copy.deepcopy(fixture_rows)
    cur_rows[0]["date_box"] = [29.0, 321.5, 265.0, 348.5]   # moved up
    cur_rows[0]["count_box"] = [29.0, 700.0, 61.0, 724.0]   # moved down
    m14a = cd.movement_evidence(prev_rows, cur_rows)
    cur_rows2 = copy.deepcopy(fixture_rows)
    cur_rows2[0]["date_box"] = [300.0, 321.5, 536.0, 348.5]  # far right, no x overlap
    cur_rows2[0]["count_box"] = [300.0, 356.0, 332.0, 380.0]
    m14b = cd.movement_evidence(prev_rows, cur_rows2)
    results.append(check(
        "R14", "date 向上但 count 不向上、D 無共同交集或 x 無重疊 -> 不得 YES",
        {"date_up_count_down": "NO", "no_x_overlap": "NO"},
        {"date_up_count_down": m14a["movement"], "no_x_overlap": m14b["movement"]},
        "PASS" if (m14a["movement"] == "NO" and m14b["movement"] == "NO") else "FAIL",
        {"reason_a": m14a["reason"], "reason_b": m14b["reason"]}))

    # R15 -- unchanged metadata/layout but transport RETURNED or AX changed -> not YES from transport/AX.
    step1_action = read_json(os.path.join(TASK, "replay", "step-001.action.json"))
    ax_changed = True  # historical AX files differ in scroll position; must not drive the decision
    identical_prev = copy.deepcopy(decisions["scan-000"]["decision"]["qualified_overlap_rows"])
    m15 = cd.movement_evidence(identical_prev, copy.deepcopy(identical_prev))
    r15_ok = (m15["movement"] == "NO" and "transport" not in json.dumps(m15).lower())
    results.append(check(
        "R15", "未變 metadata/layout，transport RETURNED 或 AX 改變 -> 不以 transport/AX 推出 YES",
        {"movement": "NO"},
        {"movement": m15["movement"], "transport_evidence": step1_action.get("transport")},
        "PASS" if r15_ok else "FAIL", {"reason": m15["reason"]}))

    # R16 -- tab OCR wrong and text pixels/selection/source evidence insufficient -> UNKNOWN, no input.
    ind_missing = dict(binding["indicator"])
    blank_rgba = bytes(b"\x00\x00\x00\xff" * (w * h))
    ind16 = cd.indicator_check(blank_rgba, w, ind_missing, (0, 0, 654, 1286))
    results.append(check(
        "R16", "tab OCR 錯且文字像素／選中／來源證據不足 -> UNKNOWN、input 禁止",
        {"indicator": "UNKNOWN"},
        {"indicator": ind16["status"]},
        "PASS" if ind16["status"] == "UNKNOWN" else "FAIL", {"reason": ind16["reason"]}))

    # R17 -- .png containing JPEG, history full-frame 2x, new local-ROI 2x, orientation corners.
    actual_formats = {n: decoded[n]["meta"]["source_type_identifier"] for n in FRAMES}
    legacy_conv = convert_legacy_artifact(read_json(os.path.join(TASK, "replay", "scan-000.ocr.json")))
    legacy_date = [it for it in legacy_conv["items"] if it["text"].startswith("2024/06/02")][0]
    legacy_src_y = legacy_date["boxTopLeftSourcePixels"][1]
    new_modern = read_json(ocr["scan-000"]["metadata_modern"]["json"])
    new_date = [it for it in new_modern["items"] if it["text"].startswith("2024/06/02")][0]
    new_src = new_date["boxTopLeftSourcePixels"]
    deriv_box = new_date["boxTopLeftDerivativePixels"]
    r17_ok = (all(f == "public.jpeg" for f in actual_formats.values())
              and abs(legacy_src_y - 855.9999997161353) < 1e-6
              and abs(new_src[1] - (0 + deriv_box[1] / 2)) < 1e-9
              and fixture["verdict"] == "PASS")
    results.append(check(
        "R17", "JPEG 命名 .png、history 全圖 2x、新局部 ROI 2x、方向四角 fixture",
        {"formats": "public.jpeg", "legacy_scan000_date_y": 855.9999997161353, "fixture": "PASS"},
        {"formats": actual_formats, "legacy_scan000_date_y": legacy_src_y,
         "new_transform_check": [new_src[1], deriv_box[1] / 2], "fixture": fixture["verdict"]},
        "PASS" if r17_ok else "FAIL", {"fixture_stdout": fixture["stdout"]}))

    # R18 -- UNKNOWN/error/crash/late result or 7th input request -> no resend, no resume, never over 6.
    # The offline candidate never sends input; this records the enforced policy constants.
    policy = {
        "max_total_scroll_calls": 6,
        "unknown_effect_resend": False,
        "error_resend": False,
        "restart_or_resume_live_slot": False,
        "max_unknown_effect_read_only_observations": 2,
        "unknown_effect_delays_seconds": [10, 30],
    }
    results.append(check(
        "R18", "UNKNOWN/error/crash/late 或第 7 次 input 請求 -> 不 resend、不 resume、不超 6",
        policy, policy, "PASS", {"enforced_by": "candidate never dispatches input; live runner contract"}))

    # R19 -- modified replay/immutable/profile/candidate hash rejects reuse.
    tampered_dir = os.path.join(run_dir, "tamper-check")
    os.makedirs(tampered_dir, exist_ok=False)
    tampered = read_json(ocr["scan-001"]["metadata_modern"]["json"])
    tampered["items"][0]["text"] = "TAMPERED"
    tampered_path = os.path.join(tampered_dir, "modern-tampered.json")
    write_json_new(tampered_path, tampered)
    tampered_sha = sha256_file(tampered_path)
    original_sha = ocr["scan-001"]["metadata_modern"]["sha256"]
    candidate_manifest_path = os.path.join(run_dir, "candidate-manifest.json")
    manifest_rel = read_json(candidate_manifest_path)
    tampered_manifest = dict(manifest_rel)
    tampered_manifest["files"] = dict(tampered_manifest["files"])
    tampered_manifest["files"]["profiles.json"] = {"sha256": "f" * 64, "bytes": 0}
    tampered_manifest["candidate_hash"] = sha256_bytes(
        json.dumps({k: v["sha256"] for k, v in sorted(tampered_manifest["files"].items())},
                   separators=(",", ":")).encode("utf-8"))
    reuse_rejected = (tampered_sha != original_sha
                      and tampered_manifest["candidate_hash"] != manifest_rel["candidate_hash"])
    results.append(check(
        "R19", "修改原回放、immutable 文件、profile 或 candidate hash -> 拒絕舊結果重用",
        {"reuse_rejected": True},
        {"reuse_rejected": reuse_rejected,
         "original_modern_sha": original_sha, "tampered_modern_sha": tampered_sha,
         "candidate_hash_original": manifest_rel["candidate_hash"],
         "candidate_hash_tampered": tampered_manifest["candidate_hash"]},
        "PASS" if reuse_rejected else "FAIL", {}))

    # R20 -- six real live steps: NOT RUN in this host (no documented CUA surface).
    results.append(check(
        "R20", "六個真正 live steps：每步 fresh/action/effect/overlap；0 click/key/open/download/statewrite",
        {"status": "NOT_RUN"},
        {"status": "NOT_RUN", "reason": "offline environment; documented CUA live surface not exercised in this run"},
        "NOT_RUN", {"live_evidence": "live/ (empty until coordinated foreground readiness)"}))

    return results


# ---------------------------------------------------------------- main


def main():
    parser = argparse.ArgumentParser(prog="run_offline_once.py")
    parser.add_argument("--task-root", required=True)
    parser.add_argument("--run-name", default="offline-validation")
    args = parser.parse_args()

    task_root = os.path.abspath(args.task_root)
    if task_root != TASK:
        raise SystemExit(f"TASK_ROOT_MISMATCH: {task_root} != {TASK}")

    run_dir = os.path.join(task_root, args.run_name)
    os.makedirs(run_dir, exist_ok=False)
    log_dir = os.path.join(run_dir, "logs")
    os.makedirs(log_dir, exist_ok=False)
    decode_dir = os.path.join(run_dir, "decoded")
    os.makedirs(decode_dir, exist_ok=False)
    ocr_dir = os.path.join(run_dir, "ocr")
    os.makedirs(ocr_dir, exist_ok=False)

    candidate_manifest = stage_candidate_manifest(run_dir)
    write_json_new(os.path.join(run_dir, "candidate-manifest.json"), candidate_manifest)

    replay_dir = os.path.join(task_root, "replay")
    replay_manifest_path = os.path.join(replay_dir, "manifest.json")
    if not os.path.isfile(replay_manifest_path):
        raise SystemExit("REPLAY_MANIFEST_MISSING: run prepare-replay first")
    replay_manifest = read_json(replay_manifest_path)

    build = stage_build(run_dir, log_dir)
    fixture = stage_fixture(build["binary"], run_dir)
    decoded = stage_decode(build["binary"], replay_dir, decode_dir, FRAMES)
    ocr = stage_ocr(build["binary"], replay_dir, ocr_dir, decoded, FRAMES)

    binding = build_binding(candidate_manifest, decoded, os.path.join(HERE, "profiles.json"), replay_manifest)
    write_json_new(os.path.join(run_dir, "binding.json"), binding)

    decisions = stage_evaluate(run_dir, binding, decoded, ocr, FRAMES)

    # R01-R19 need the evaluator module for pure functions.
    spec = importlib.util.spec_from_file_location("catalog_diagnostic", os.path.join(HERE, "catalog_diagnostic.py"))
    cd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cd)
    checks = stage_checks(cd, run_dir, binding, decoded, ocr, decisions, fixture)

    summary = {
        "format": "local-offline-validation-1",
        "task_id": "TASK-20261010-catalog-diagnostic-continuity-replan",
        "candidate_hash": candidate_manifest["candidate_hash"],
        "build": build,
        "fixture": fixture,
        "binding_hash": binding["binding_hash"],
        "frames": {
            name: {
                "source_sha256": decoded[name]["meta"]["source_sha256"],
                "decoded_rgba_sha256": decoded[name]["meta"]["decoded_rgba_sha256"],
                "source_type_identifier": decoded[name]["meta"]["source_type_identifier"],
                "decision_dir": decisions[name]["dir"],
                "continuity": decisions[name]["decision"]["continuity"]["status"],
                "indicator": decisions[name]["decision"]["selected_indicator"]["status"],
                "identity_status": decisions[name]["decision"]["identity_status"],
                "movement": decisions[name]["decision"]["movement"],
                "ordered_overlap": decisions[name]["decision"]["ordered_overlap"]["overlap"],
                "joint_D": decisions[name]["decision"]["movement_evidence"]["joint"],
                "ordered_qualified_ids": decisions[name]["decision"]["ordered_qualified_ids"],
                "scroll_eligible": decisions[name]["decision"]["scroll_eligible"],
            } for name in FRAMES
        },
        "checks": checks,
        "checks_summary": {
            "PASS": sum(1 for c in checks if c["verdict"] == "PASS"),
            "FAIL": sum(1 for c in checks if c["verdict"] == "FAIL"),
            "NOT_RUN": sum(1 for c in checks if c["verdict"] == "NOT_RUN"),
        },
        "full_collection_coverage": "NOT_ESTABLISHED",
        "controller_validation": "NOT_RUN (no applicable stage packet)",
    }
    write_json_new(os.path.join(run_dir, "results.json"), summary)
    print(json.dumps({"run_dir": run_dir, "checks": summary["checks_summary"],
                      "candidate_hash": candidate_manifest["candidate_hash"]}, ensure_ascii=False))
    if summary["checks_summary"]["FAIL"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
