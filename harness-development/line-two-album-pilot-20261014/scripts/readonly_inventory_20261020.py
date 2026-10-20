#!/usr/bin/env python3
"""Read-only re-hash of the manually downloaded A56/B53 archives.

Compares physical files against the published SHA-256 manifests and the
per-album verification JSON. Writes nothing except the JSON report path
given on the command line.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ALBUMS = [
    {
        "label": "A56",
        "dates": "2024/05/27～05/31",
        "backup_suffix": "2024-05-27_2024-05-31_56張",
        "public_dir": "harness-development/line-two-album-pilot-20261014/public/manual-diagnostic-20261020-a56",
        "manifest_txt": "a56-sha256.txt",
        "verification_json": "a56-verification.json",
    },
    {
        "label": "B53",
        "dates": "2024/05/20～05/24",
        "backup_suffix": "2024-05-20_2024-05-24_53張",
        "public_dir": "harness-development/line-two-album-pilot-20261014/public/manual-diagnostic-20261020-b53",
        "manifest_txt": "b53-sha256.txt",
        "verification_json": "b53-verification.json",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest_txt(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, name = line.split(None, 1)
        entries[name.strip()] = digest.lower()
    return entries


def resolve_backup_dir(repo_root: Path, suffix: str) -> Path:
    matches = sorted(p for p in (repo_root / "backups").glob(f"*/{suffix}") if p.is_dir())
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one backup dir for {suffix}, found {len(matches)}")
    return matches[0]


def audit_album(repo_root: Path, evidence_root: Path, spec: dict) -> dict:
    backup_dir = resolve_backup_dir(repo_root, spec["backup_suffix"])
    public_dir = evidence_root / spec["public_dir"]
    manifest = load_manifest_txt(public_dir / spec["manifest_txt"])
    verification = json.loads((public_dir / spec["verification_json"]).read_text(encoding="utf-8"))

    json_entries = {e["file"]: e for e in verification["files"]["entries"]}
    physical = sorted(p for p in backup_dir.iterdir() if p.is_file())
    physical_names = {p.name for p in physical}

    mismatched: list[str] = []
    missing: list[str] = []
    unexpected: list[str] = []
    total_bytes = 0
    per_file: list[dict] = []

    for path in physical:
        digest = sha256_file(path)
        size = path.stat().st_size
        total_bytes += size
        expected = manifest.get(path.name)
        if expected is None:
            unexpected.append(path.name)
            status = "NOT_IN_MANIFEST"
        elif expected != digest:
            mismatched.append(path.name)
            status = "SHA_MISMATCH"
        else:
            status = "MATCH"
        json_entry = json_entries.get(path.name)
        if json_entry is not None and (
            json_entry.get("sha256") != digest or json_entry.get("bytes") != size
        ):
            mismatched.append(path.name)
            status = "JSON_MISMATCH"
        per_file.append({"file": path.name, "bytes": size, "sha256": digest, "status": status})

    for name in manifest:
        if name not in physical_names:
            missing.append(name)

    declared_bytes = verification["files"]["total_bytes"]
    declared_count = verification["files"]["count"]

    return {
        "label": spec["label"],
        "dates": spec["dates"],
        "physical_dir": f"backups/<REDACTED_GROUP>/{spec['backup_suffix']}",
        "manifest": f"{spec['public_dir']}/{spec['manifest_txt']}",
        "physical_file_count": len(physical),
        "physical_total_bytes": total_bytes,
        "declared_file_count": declared_count,
        "declared_total_bytes": declared_bytes,
        "count_matches_declared": len(physical) == declared_count,
        "bytes_match_declared": total_bytes == declared_bytes,
        "manifest_entry_count": len(manifest),
        "sha_mismatches": sorted(set(mismatched)),
        "missing_files": sorted(missing),
        "unexpected_files": sorted(unexpected),
        "status": "PASS"
        if not mismatched and not missing and not unexpected
        and len(physical) == declared_count
        and total_bytes == declared_bytes
        else "FAIL",
        "entries": per_file,
    }


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve()
    evidence_root = Path(sys.argv[2]).resolve()
    out = Path(sys.argv[3]).resolve()
    albums = [audit_album(repo_root, evidence_root, spec) for spec in ALBUMS]
    report = {
        "schema": "READONLY_MANUAL_ARCHIVE_INVENTORY/1",
        "mode": "READ_ONLY_NO_GUI_NO_STATE_WRITE",
        "workspace_root_redacted": True,
        "group_name_redacted": True,
        "state_revision_read": 35,
        "albums": albums,
        "overall_status": "PASS" if all(a["status"] == "PASS" for a in albums) else "FAIL",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for album in albums:
        print(
            album["label"],
            album["status"],
            album["physical_file_count"],
            album["physical_total_bytes"],
            "mismatch=%d missing=%d unexpected=%d"
            % (len(album["sha_mismatches"]), len(album["missing_files"]), len(album["unexpected_files"])),
        )
    print("OVERALL", report["overall_status"])
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
