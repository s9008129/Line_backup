#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
TASK = ROOT / "harness-development/line-e2e-fullscreen-repair-20261010"
SOURCE = TASK / "candidate/v2"
SDK = Path("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error("attempt must be positive")
    bin_dir = SOURCE / "bin"
    build_dir = TASK / "build"
    bin_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    checks = []
    for name, filename in (("fullscreen-capture", "FullscreenCapture.swift"), ("vision-regions", "VisionRegions.swift"), ("image-decode", "image_decode.swift")):
        source = SOURCE / filename
        output = bin_dir / name
        command = [
            "/usr/bin/xcrun", "--sdk", "macosx26.5", "swiftc",
            "-sdk", str(SDK), "-target", "arm64-apple-macosx26.0",
            "-swift-version", "6",
        ]
        if name != "image-decode":
            command.append("-parse-as-library")
        command.extend([str(source), "-o", str(output)])
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        checks.append({
            "name": name,
            "command": command,
            "source": str(source),
            "source_sha256": digest(source),
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "binary": str(output) if completed.returncode == 0 else None,
            "binary_sha256": digest(output) if completed.returncode == 0 else None,
        })
    info = subprocess.run(["/usr/bin/xcodebuild", "-version"], cwd=ROOT, capture_output=True, text=True)
    swift = subprocess.run(["/usr/bin/xcrun", "--sdk", "macosx26.5", "swiftc", "-version"], cwd=ROOT, capture_output=True, text=True)
    result = {
        "attempt": args.attempt,
        "sdk_path": str(SDK),
        "sdk_exists": SDK.is_dir(),
        "xcodebuild_exit_code": info.returncode,
        "xcodebuild_stdout": info.stdout,
        "xcodebuild_stderr": info.stderr,
        "swiftc_exit_code": swift.returncode,
        "swiftc_stdout": swift.stdout,
        "swiftc_stderr": swift.stderr,
        "checks": checks,
        "verdict": "PASS" if all(check["exit_code"] == 0 for check in checks) else "FAIL",
    }
    destination = build_dir / f"attempt-{args.attempt:02}.json"
    if destination.exists():
        raise SystemExit(f"refusing to overwrite {destination}")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"verdict": result["verdict"], "evidence": str(destination), "checks": [{"name": c["name"], "exit_code": c["exit_code"]} for c in checks]}, ensure_ascii=False))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
