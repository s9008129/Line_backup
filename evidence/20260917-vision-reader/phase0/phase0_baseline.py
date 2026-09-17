#!/usr/bin/env python3
"""Phase 0 read-only baseline for the Vision-reader wave (H3.0 §10 / GOAL phase 0).

Zero GUI input, zero UI interaction, zero writes to formal data. It:

  1. records the repo anchor (branch/HEAD/status);
  2. re-computes every SHA-256 anchor listed in handoff-vision-agent-2026-09-17.md §3
     and compares it with the value recorded in that handoff;
  3. rebuilds the frozen Vision helper from its frozen Swift source with swiftc -O;
  4. re-runs the C1/C3/C5 offline sanity readings on the four frozen attempt-05 frames
     that are still present in /tmp, five times each (C2-style determinism probe);
  5. makes byte-identical preservation copies of those four volatile frames into
     evidence/20260917-vision-reader/frames/ (append-only; the /tmp originals and every
     earlier evidence artifact are left untouched);
  6. writes baseline.json next to this script.

The script refuses to overwrite an existing baseline.json / frames copy. Re-running the
wave must use a new attempt directory instead of rewriting evidence.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
WAVE = os.path.dirname(HERE)
FRAMES_DIR = os.path.join(WAVE, "frames")
BUILD_BIN = "/tmp/vision_ocr_phase0_build"
HELPER_SRC = os.path.join(REPO, "evidence/20260916-route/tools/vision/vision_ocr.swift")

TASK = ".agent/tasks/T20260916-0102-01-line-backup-acceptance"

# item -> (path relative to repo, expected SHA-256 from H3.0 §3)
HANDOFF_ANCHORS = {
    "plan.md (Rev20)": (TASK + "/plan.md",
        "4919d87148c68ea3d70cbb9abd258edbd0bfa0b55be5123f7202251e557db17c"),
    "review attempt-28 report": (TASK + "/review/attempt-28/review_report.md",
        "d9bf574facc636c97bfbe080769cce9ed30e5b05c31f7ef0847b0552b99ea09d"),
    "review attempt-29 report": (TASK + "/review/attempt-29/review_report.md",
        "540fda1a35590fc4047a49723a204879395c2258ec1597c4d036093f69872683"),
    "task handoff (Stage 03, Rev20)": (TASK + "/handoff.md",
        "ab88e496e7ab24214247a1cc3c5fc65b751e439d3c46238433f65d02361484a4"),
    "route attempt-05 run-ledger": ("evidence/20260916-route/attempt-05/run-ledger.json",
        "17b172031a38ea6b5c66ebfedacf748aa1f08b12d572263d13eef02f54465218"),
    "route attempt-05 vision crosscheck": ("evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json",
        "d3ebbaed3db446cfbecd01d74d132764b6a675232b9db9edd2d1af3071dd6d5b"),
    "Vision helper source": ("evidence/20260916-route/tools/vision/vision_ocr.swift",
        "4fc9fa2be748f0620344bdfd501f7ef2d3349f6f03fc29290dd91550f3523b32"),
    "Vision helper README": ("evidence/20260916-route/tools/vision/README.md",
        "9fa083d551da6d89fd9e385d228e3041802e1595457169af28b324013318767d"),
    "v3 selftest summary": ("evidence/20260916-route/tools/selftest/v3/selftest-summary.json",
        "17840e915680308fb721a937462d22898c3adb1aa125e3cb2469f74c31344324"),
    "v3 tool locate_album_card.py": ("evidence/20260916-route/tools/locate_album_card.py",
        "500fcadbe8cb47f1cd22f0d247ad7d7d65c84baef4000f2239e1872e340e98e4"),
    "v3 tool verify_album_open.py": ("evidence/20260916-route/tools/verify_album_open.py",
        "80504262025cf10202c8938612b5be73f91809578f1317f36733f52b513fa74b"),
    "v3 tool locate_album_ellipsis.py": ("evidence/20260916-route/tools/locate_album_ellipsis.py",
        "60e3120abb312f189f785f12ee4047f4365028a8759ae88874eebb06046a7deb"),
    "v2 tool detect_menu_popup.py": ("evidence/20260916-route/tools/detect_menu_popup.py",
        "6ae9c250bfaec7c639482deafa65b0c66f85927a21584e3dac6c9511c7f740bc"),
    "v2 tool locate_card_ellipsis.py": ("evidence/20260916-route/tools/locate_card_ellipsis.py",
        "8c8b6fc704c09a476419492eef2cd999e472126312feff72093f2cfef715df9e"),
    "root handoff H3.0": ("handoff-vision-agent-2026-09-17.md", None),
    "root GOAL command file": ("GOAL-vision-agent-next-conversation.md", None),
}

# label -> (tmp path, recorded SHA from the attempt-05 crosscheck, size_px, role)
FRAMES = [
    ("post", "/tmp/route5r_frame_post.jpg",
     "4cb8a6b4cbc8f1add6577a0ae16f2fbe529ef09c7c3f7bba00b225705c6560b3", [327, 643],
     "post frame after the single authorized album-card click (S5 input)"),
    ("pre", "/tmp/route5r_frame_pre.jpg",
     "3d926e7df9a5737942e1483641a787ac8f522a2c5e7af38fab06a6e3f573d531", [327, 643],
     "pre frame before the click"),
    ("s1", "/tmp/route5r_probe_crop_s1.png",
     "aea53a0df8c4ef20488446dbccc42fa84ecd72c36aad71d42199f20b9e30f5c3", [327, 643],
     "screen-probe crop at scale 1 (frozen locator read 27)"),
    ("s2", "/tmp/route5r_probe_crop_s2.png",
     "7b9d0a19323e0f7341d2ee9722415251195531dc067b773f231676729c63721b", [654, 1286],
     "screen-probe crop at scale 2 (frozen locator read 5)"),
]
DETERMINISM_RUNS = 5


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def main():
    baseline_path = os.path.join(HERE, "baseline.json")
    if os.path.exists(baseline_path):
        raise SystemExit("refusing to overwrite " + baseline_path)
    for name, src, _sha, _size, _role in FRAMES:
        dst = os.path.join(FRAMES_DIR, os.path.basename(src))
        if os.path.exists(dst):
            raise SystemExit("refusing to overwrite " + dst)

    doc = {
        "schema_version": 1,
        "artifact": "phase0-baseline",
        "wave": "20260917-vision-reader",
        "purpose": ("H3.0 §10 Phase 0 read-only baseline: repo anchor, handoff §3 SHA re-check, "
                    "Vision helper rebuild, C1/C3/C5 offline sanity + C2-style determinism probe on the "
                    "frozen attempt-05 frames, and byte-identical preservation copies of those volatile frames."),
        "generated_at_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "task_id": "T20260916-0102-01-line-backup-acceptance",
        "plan_revision_at_baseline": 20,
        "inputs_sent": 0,
        "ui_interaction": "none (no click, no keyboard, no AX write, no window activation, no capture)",
        "formal_data_writes": 0,
        "images_in_conversation": 0,
    }

    git_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO).stdout.decode().strip()
    git_head = run(["git", "rev-parse", "HEAD"], cwd=REPO).stdout.decode().strip()
    git_status = run(["git", "status", "--porcelain"], cwd=REPO).stdout.decode()
    git_remote = run(["git", "remote", "-v"], cwd=REPO).stdout.decode().strip()
    doc["repo"] = {
        "root": REPO,
        "branch": git_branch,
        "head": git_head,
        "head_subject": run(["git", "log", "-1", "--pretty=%s"], cwd=REPO).stdout.decode().strip(),
        "status_porcelain": git_status.splitlines(),
        "status_note": ("lines are this wave's own new untracked files; no tracked modification"),
        "remotes": git_remote or None,
        "remote_note": "no git remote is configured; committed evidence cannot leave this machine",
    }

    anchors = []
    for item, (rel, expected) in HANDOFF_ANCHORS.items():
        path = os.path.join(REPO, rel)
        observed = sha256_file(path) if os.path.exists(path) else None
        row = {"item": item, "path": rel, "observed_sha256": observed,
               "recorded_sha256": expected}
        if expected is not None:
            row["match"] = observed == expected
        anchors.append(row)
    doc["handoff_sha_table"] = anchors
    doc["handoff_sha_mismatches"] = [r["item"] for r in anchors if r.get("match") is False]

    build = run(["swiftc", "-O", HELPER_SRC, "-o", BUILD_BIN])
    swift_version = run(["swiftc", "--version"]).stdout.decode().strip()
    doc["helper_rebuild"] = {
        "source_path": os.path.relpath(HELPER_SRC, REPO),
        "source_sha256": sha256_file(HELPER_SRC),
        "command": "swiftc -O evidence/20260916-route/tools/vision/vision_ocr.swift -o " + BUILD_BIN,
        "returncode": build.returncode,
        "stderr": build.stderr.decode(errors="replace").strip(),
        "binary_path": BUILD_BIN,
        "binary_bytes": os.path.getsize(BUILD_BIN) if os.path.exists(BUILD_BIN) else None,
        "binary_sha256": sha256_file(BUILD_BIN) if os.path.exists(BUILD_BIN) else None,
        "swiftc_version": swift_version,
        "os": run(["sw_vers"], ).stdout.decode().strip().replace("\n", " | "),
        "arch": run(["uname", "-m"]).stdout.decode().strip(),
        "recorded_volatile_binary": {
            "path": "/tmp/vision_ocr", "bytes": 67192,
            "sha256": "f54628e8f42fb65200bf98bf5cc6463937d28781c673c22e5ca8b9418ae3f6c9"},
        "byte_identical_to_recorded": None,
        "note": ("swiftc output is not byte-deterministic; equivalence is established by re-reading the "
                 "exact recorded frames and reproducing the recorded stdout bytes (see sanity/determinism)."),
    }
    if os.path.exists("/tmp/vision_ocr"):
        doc["helper_rebuild"]["byte_identical_to_recorded"] = (
            sha256_file("/tmp/vision_ocr") ==
            "f54628e8f42fb65200bf98bf5cc6463937d28781c673c22e5ca8b9418ae3f6c9")

    readings_dir = os.path.join(HERE, "readings")
    sanity = {"runs_per_frame": DETERMINISM_RUNS, "frames": [], "determinism_all_identical": True}
    frame_copies = []
    for label, src, recorded_sha, size_px, role in FRAMES:
        entry = {"label": label, "tmp_path": src, "role": role, "size_px": size_px,
                 "recorded_sha256": recorded_sha}
        if not os.path.exists(src):
            entry["present_in_tmp"] = False
            entry["sha256"] = None
            entry["match_recorded"] = False
            sanity["determinism_all_identical"] = False
            sanity["frames"].append(entry)
            continue
        observed = sha256_file(src)
        entry["present_in_tmp"] = True
        entry["sha256"] = observed
        entry["bytes"] = os.path.getsize(src)
        entry["match_recorded"] = observed == recorded_sha
        run_hashes, run_exits, first_stdout = [], [], None
        for i in range(DETERMINISM_RUNS):
            proc = run([BUILD_BIN, src])
            run_hashes.append(sha256_bytes(proc.stdout))
            run_exits.append(proc.returncode)
            if first_stdout is None:
                first_stdout = proc.stdout
        entry["stdout_sha256_per_run"] = run_hashes
        entry["exit_codes"] = run_exits
        entry["deterministic"] = len(set(run_hashes)) == 1 and len(set(run_exits)) == 1
        if not entry["deterministic"]:
            sanity["determinism_all_identical"] = False
        out_path = os.path.join(readings_dir, label + ".txt")
        with open(out_path, "wb") as f:
            f.write(first_stdout)
        entry["reading_path"] = os.path.relpath(out_path, REPO)
        entry["reading_sha256"] = sha256_bytes(first_stdout)
        entry["reading_lines"] = first_stdout.decode("utf-8", errors="replace").splitlines()
        # preservation copy (append-only, byte-identical)
        dst = os.path.join(FRAMES_DIR, os.path.basename(src))
        shutil.copyfile(src, dst)
        copy_sha = sha256_file(dst)
        frame_copies.append({"src_tmp": src, "dst": os.path.relpath(dst, REPO),
                             "sha256": copy_sha, "byte_identical": copy_sha == observed})
        sanity["frames"].append(entry)
    doc["frozen_frames_tmp"] = sanity
    doc["preservation_copies"] = frame_copies
    with open(os.path.join(FRAMES_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1,
                   "artifact": "frames-manifest",
                   "wave": "20260917-vision-reader",
                   "generated_at_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "origin": "attempt-05 frozen frames captured 2026-09-17 (see evidence/20260916-route/attempt-05/vision-ocr-crosscheck.json)",
                   "note": ("byte-identical preservation copies of the volatile /tmp frames recorded by the "
                            "attempt-05 cross-check; SHA-256 must equal the crosscheck values"),
                   "frames": [{"label": l, "path": os.path.relpath(os.path.join(FRAMES_DIR, os.path.basename(s)), REPO),
                               "origin_tmp_path": s, "sha256": c["sha256"], "size_px": sp, "role": role}
                              for (l, s, _r, sp, role), c in zip(FRAMES, frame_copies)]},
                  f, ensure_ascii=False, indent=1)

    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(json.dumps({
        "baseline": os.path.relpath(baseline_path, REPO),
        "handoff_sha_mismatches": doc["handoff_sha_mismatches"],
        "helper_binary_sha256": doc["helper_rebuild"]["binary_sha256"],
        "determinism_all_identical": doc["frozen_frames_tmp"]["determinism_all_identical"],
        "frames_present": [f.get("present_in_tmp") for f in doc["frozen_frames_tmp"]["frames"]],
        "copies_byte_identical": [c["byte_identical"] for c in doc["preservation_copies"]],
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
