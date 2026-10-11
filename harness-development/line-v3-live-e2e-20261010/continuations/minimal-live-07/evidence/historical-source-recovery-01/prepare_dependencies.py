#!/usr/bin/env python3
"""Pinned, task-local schema dependency preparation for ML07 amendments 01/02."""
from __future__ import annotations

import hashlib
import io
import json
import os
import pathlib
import stat
import subprocess
import sys
import urllib.request
import zipfile

ROOT = pathlib.Path("/Users/hsiaojohnny/Documents/ChatGPT/Line_backup")
RUNREL = "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-07"
R = ROOT / RUNREL
EPOCHREL = RUNREL + "/epochs/e01"
EPOCH = ROOT / EPOCHREL
PY = pathlib.Path("/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13/bin/python3.13")
CACHE = pathlib.Path("/Users/hsiaojohnny/Library/Caches/pip/http-v2")
PINS = [
    ("jsonschema", "4.26.0", "jsonschema-4.26.0-py3-none-any.whl", 90630, "d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce", None),
    ("referencing", "0.37.0", "referencing-0.37.0-py3-none-any.whl", 26766, "381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231", None),
    ("jsonschema-specifications", "2025.9.1", "jsonschema_specifications-2025.9.1-py3-none-any.whl", 18437, "98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe", None),
    ("attrs", "26.1.0", "attrs-26.1.0-py3-none-any.whl", 67548, "c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309", None),
    ("rpds-py", "2026.6.3", "rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl", 338203, "f4d78253f6996be4901669ad25319f842f740eccf4d58e3c7f3dd39e6dde1d8f", "https://files.pythonhosted.org/packages/f3/6b/686d9dc4359a8f163cfbbf89ee0b4e586431de22fe8248edb63a8cf50d49/rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl"),
    ("rfc3339-validator", "0.1.4", "rfc3339_validator-0.1.4-py2.py3-none-any.whl", 3490, "24f6ec1eda14ef823da9e36ec7113124b39c04d50a4d3d3a3c2859577e7791fa", "https://files.pythonhosted.org/packages/7b/44/4e421b96b67b2daff264473f7465db72fbdf36a07e05494f50300cc7b0c6/rfc3339_validator-0.1.4-py2.py3-none-any.whl"),
    ("six", "1.17.0", "six-1.17.0-py2.py3-none-any.whl", 11050, "4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274", "https://files.pythonhosted.org/packages/b7/ce/149a00dd41f10bc29e5921b496af8b574d8413afcd5e30dfa0ed46c2cc5e/six-1.17.0-py2.py3-none-any.whl"),
]

sys.path.insert(0, str(R / "tools"))
from evidence_io import publish_exclusive
from output_policy import OutputPolicy, _read_anchored


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def checked_zip(raw: bytes, filename: str) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("DUPLICATE_ZIP_ENTRY:" + filename)
        for info in archive.infolist():
            parts = info.filename.split("/")
            mode = (info.external_attr >> 16) & 0xffff
            kind = stat.S_IFMT(mode)
            if info.filename.startswith("/") or any(p in ("", ".", "..") for p in parts[:-1]) or ".." in parts or "\\" in info.filename or kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("UNSAFE_WHEEL_ENTRY:" + info.filename)
            if info.file_size > 16 * 1024 * 1024:
                raise ValueError("WHEEL_MEMBER_CAP:" + info.filename)
        if not any(n.endswith(".dist-info/WHEEL") for n in names):
            raise ValueError("MISSING_WHEEL_METADATA:" + filename)


def source_bytes(pin: tuple) -> tuple[bytes, str]:
    package, version, filename, length, digest, url = pin
    for candidate in CACHE.rglob("*.body"):
        if candidate.stat().st_size == length:
            raw = candidate.read_bytes()
            if sha(raw) == digest:
                return raw, str(candidate)
    if url is None:
        raise RuntimeError("PINNED_CACHE_MISSING:" + filename)
    if not url.startswith("https://files.pythonhosted.org/packages/") or not url.endswith("/" + filename):
        raise RuntimeError("UNAPPROVED_URL")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ML07-fixed-wheel/1"}), timeout=30) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise RuntimeError("FETCH_CAP")
    return raw, url


def tree_manifest(root: pathlib.Path) -> list[dict]:
    records = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        st = p.lstat()
        if stat.S_ISLNK(st.st_mode):
            records.append({"path": rel, "type": "SYMLINK", "target": os.readlink(p)})
        elif stat.S_ISDIR(st.st_mode):
            records.append({"path": rel, "type": "DIRECTORY"})
        elif stat.S_ISREG(st.st_mode):
            raw = p.read_bytes()
            records.append({"path": rel, "type": "REGULAR", "bytes": len(raw), "sha256": sha(raw)})
        else:
            raise RuntimeError("INSTALLED_SPECIAL:" + rel)
    if sum(r.get("bytes", 0) for r in records) > 64 * 1024 * 1024:
        raise RuntimeError("INSTALLED_TREE_CAP")
    return records


def finalize() -> int:
    policy = OutputPolicy.load(EPOCH / "output-policy.json", ROOT)
    observation = json.loads((EPOCH / "runtime/dependency-install-observation.json").read_bytes())
    if observation.get("exit_code") != 0 or observation.get("installed_tree") != tree_manifest(EPOCH / "runtime/site-packages"):
        raise RuntimeError("INSTALL_OBSERVATION_DRIFT")
    refs = []
    names = ["evidence/dependency-bootstrap-policy.json"]
    names += ["epochs/e01/runtime/requirements.lock", "epochs/e01/runtime/dependency-input-manifest.json", "epochs/e01/runtime/dependency-install-observation.json"]
    names += ["epochs/e01/runtime/wheels/" + p[2] for p in PINS]
    names += ["epochs/e01/runtime/site-packages/" + r["path"] for r in observation["installed_tree"] if r["type"] == "REGULAR"]
    for suffix in names:
        rel = f"{RUNREL}/{suffix}"
        raw, st = _read_anchored(ROOT, rel, 16 * 1024 * 1024)
        refs.append({"path": rel, "bytes": len(raw), "sha256": sha(raw), "dev": st.st_dev, "ino": st.st_ino, "readback_verified": True})
    receipt = {"format": "ML07_DEPENDENCY_PREPARATION_RECEIPT_V1", "task_id": policy.task_id, "epoch": str(EPOCH), "phase": "RUNTIME_PREPARE", "producer": "tools/prepare_dependencies.py", "source_freeze_sha256": policy.source_freeze_sha256, "bootstrap_policy_sha256": sha((R / "evidence/dependency-bootstrap-policy.json").read_bytes()), "artifacts": refs}
    rel = f"{EPOCHREL}/runtime/dependency-preparation-receipt.json"
    raw = encoded(receipt)
    decision = policy.authorize_prewrite(path=rel, phase="RUNTIME_PREPARE", producer="tools/prepare_dependencies.py", entry_type="REGULAR", byte_count=len(raw), operation="CREATE", preexisting=(ROOT / rel).exists())
    if not decision.allowed:
        raise RuntimeError("RECEIPT_POLICY:" + decision.code)
    result = publish_exclusive(ROOT, rel, raw, max_bytes=1024 * 1024)
    print(json.dumps({"receipt": result, "artifact_count": len(refs)}, sort_keys=True))
    return 0


def main() -> int:
    if pathlib.Path.cwd() != ROOT or pathlib.Path(os.path.realpath(sys.argv[0])) != R / "tools/prepare_dependencies.py":
        raise RuntimeError("WRONG_LOCATION")
    if len(sys.argv) == 2 and sys.argv[1] == "finalize":
        return finalize()
    if len(sys.argv) != 1:
        raise RuntimeError("ARGUMENTS")
    runtime = EPOCH / "runtime"
    if runtime.exists():
        raise RuntimeError("RUNTIME_ALREADY_EXISTS")
    wheels = runtime / "wheels"
    site = runtime / "site-packages"
    pip_temp = EPOCH / "tmp/pip-cache"
    planning = {name: {"bytes": len((R / name).read_bytes()), "sha256": sha((R / name).read_bytes())} for name in ("replan-amendment-01.md", "replan-amendment-02.md")}
    policy = {"format": "ML07_DEPENDENCY_BOOTSTRAP_POLICY_V1", "task_id": "TASK-20261010-line-v3-live-e2e", "epoch": str(EPOCH), "producer": "tools/prepare_dependencies.py", "planning": planning,
              "wheels": [{"path": f"{EPOCHREL}/runtime/wheels/{p[2]}", "bytes": p[3], "sha256": p[4], "source": p[5] or "LOCAL_PINNED_CACHE"} for p in PINS],
              "outputs": [f"{EPOCHREL}/runtime/requirements.lock", f"{EPOCHREL}/runtime/dependency-input-manifest.json", f"{EPOCHREL}/runtime/dependency-install-observation.json"],
              "directories": [f"{EPOCHREL}/runtime", f"{EPOCHREL}/runtime/wheels", f"{EPOCHREL}/runtime/site-packages", f"{EPOCHREL}/tmp/pip-cache"],
              "install_root": f"{EPOCHREL}/runtime/site-packages", "install_cap_bytes": 64 * 1024 * 1024, "scratch_root": f"{EPOCHREL}/tmp/pip-cache"}
    policy_ref = publish_exclusive(ROOT, f"{RUNREL}/evidence/dependency-bootstrap-policy.json", encoded(policy), max_bytes=1024 * 1024)
    runtime.mkdir(mode=0o700)
    wheels.mkdir(mode=0o700)
    site.mkdir(mode=0o700)
    pip_temp.mkdir(mode=0o700)
    wheel_refs = []
    for pin in PINS:
        package, version, filename, length, digest, _ = pin
        raw, origin = source_bytes(pin)
        if len(raw) != length or sha(raw) != digest:
            raise RuntimeError("WHEEL_PIN_MISMATCH:" + filename)
        checked_zip(raw, filename)
        ref = publish_exclusive(ROOT, f"{EPOCHREL}/runtime/wheels/{filename}", raw, max_bytes=1024 * 1024)
        wheel_refs.append({**ref, "package": package, "version": version, "origin": origin})
    lock = "".join(f"{p[0]}=={p[1]} --hash=sha256:{p[4]}\n" for p in PINS).encode()
    lock_ref = publish_exclusive(ROOT, f"{EPOCHREL}/runtime/requirements.lock", lock, max_bytes=1024 * 1024)
    manifest = {"format": "ML07_DEPENDENCY_INPUT_V1", "task_id": policy["task_id"], "epoch": str(EPOCH), "policy_ref": policy_ref, "planning": planning, "wheels": wheel_refs, "lock": lock_ref, "python": {"path": str(PY), "sha256": sha(PY.read_bytes())}}
    manifest_ref = publish_exclusive(ROOT, f"{EPOCHREL}/runtime/dependency-input-manifest.json", encoded(manifest), max_bytes=1024 * 1024)
    argv = [str(PY), "-B", "-m", "pip", "--isolated", "install", "--no-index", "--no-deps", "--only-binary=:all:", "--require-hashes", "--no-compile", "--disable-pip-version-check", "--no-cache-dir", "--target", str(site), "--find-links", str(wheels), "-r", str(runtime / "requirements.lock")]
    env = dict(os.environ)
    env.update({"TMPDIR": str(pip_temp), "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INPUT": "1"})
    try:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
        outcome = {"argv": argv, "cwd": str(ROOT), "env_overrides": {k: env[k] for k in ("TMPDIR", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PIP_NO_INPUT")}, "exit_code": result.returncode, "stdout": result.stdout[:2*1024*1024].decode(errors="replace"), "stderr": result.stderr[:2*1024*1024].decode(errors="replace"), "stdout_truncated": len(result.stdout)>2*1024*1024, "stderr_truncated": len(result.stderr)>2*1024*1024}
    except subprocess.TimeoutExpired as exc:
        outcome = {"argv": argv, "cwd": str(ROOT), "timeout_seconds": 180, "stdout": (exc.stdout or b"")[:2*1024*1024].decode(errors="replace"), "stderr": (exc.stderr or b"")[:2*1024*1024].decode(errors="replace"), "stop_reason": "TIMEOUT"}
    outcome["installed_tree"] = tree_manifest(site)
    observation_ref = publish_exclusive(ROOT, f"{EPOCHREL}/runtime/dependency-install-observation.json", encoded(outcome), max_bytes=8*1024*1024)
    print(json.dumps({"manifest": manifest_ref, "observation": observation_ref, "installed_count": len(outcome["installed_tree"]), "exit_code": outcome.get("exit_code")}, sort_keys=True))
    return 0 if outcome.get("exit_code") == 0 and not outcome.get("stdout_truncated") and not outcome.get("stderr_truncated") else 1


if __name__ == "__main__":
    raise SystemExit(main())
