#!/usr/bin/env python3
"""Check this local archive; restore only with --apply and no collisions."""
from pathlib import Path
import argparse
import json
import os
from cleanup import inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    task = Path(__file__).resolve().parent
    manifest = json.loads((task / 'archive-manifest.json').read_text())
    root = Path(manifest['repository'])
    archive = Path(manifest['archive_root'])
    planned = []
    for mapping in manifest['mappings']:
        destination = root / mapping['source_relative']
        source = archive / mapping['archive_relative']
        assert destination.resolve().is_relative_to(root.resolve())
        assert source.resolve().is_relative_to(archive.resolve())
        assert not destination.exists() and not destination.is_symlink(), f'Collision: {destination}'
        assert inventory(source) == mapping['entries'], f'Archive mismatch: {source}'
        assert source.stat().st_dev == root.stat().st_dev, 'Atomic same-volume restore required'
        planned.append((source, destination))
    print(json.dumps({'mode': 'RESTORE' if args.apply else 'CHECK_ONLY',
                      'mappings': [{'from': str(source), 'to': str(destination)} for source, destination in planned]},
                     ensure_ascii=False, indent=2))
    if args.apply:
        moved = []
        try:
            for source, destination in planned:
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.rename(source, destination)
                moved.append((source, destination))
        except Exception:
            for source, destination in reversed(moved):
                if destination.exists() and not source.exists():
                    os.rename(destination, source)
            raise


if __name__ == '__main__':
    main()
