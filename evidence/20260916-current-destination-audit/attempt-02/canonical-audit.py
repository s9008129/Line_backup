#!/usr/bin/env python3
import hashlib
import json
import mimetypes
import os
import stat
import subprocess
import sys
import time


def fail(message):
    raise RuntimeError(message)


def inventory(destination, expected, sample):
    root = os.path.abspath(destination)
    if not os.path.isdir(root):
        fail(f"destination is not a directory: {root}")
    entries = []
    errors = []
    other_entries = 0
    partial_temp_files = 0
    symlinks = 0
    subdirectories = 0
    zero_byte_files = 0
    regular_files = 0
    recognized_images = 0
    unrecognized_regular_files = 0
    total_bytes = 0
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        try:
            st = os.lstat(path)
        except OSError as exc:
            errors.append(f"lstat {name}: {exc}")
            continue
        if stat.S_ISLNK(st.st_mode):
            symlinks += 1
            continue
        if stat.S_ISDIR(st.st_mode):
            subdirectories += 1
            continue
        if not stat.S_ISREG(st.st_mode):
            other_entries += 1
            continue
        regular_files += 1
        if st.st_size == 0:
            zero_byte_files += 1
        if name.endswith(('.part', '.partial', '.tmp', '.crdownload')):
            partial_temp_files += 1
        try:
            mime = subprocess.run(
                ['/usr/bin/file', '--brief', '--mime-type', '--', path],
                check=True, capture_output=True, text=True).stdout.strip()
            digest = hashlib.sha256()
            with open(path, 'rb') as handle:
                while True:
                    block = handle.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            actual_size = os.stat(path).st_size
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"read {name}: {exc}")
            continue
        total_bytes += actual_size
        if mime.startswith('image/') and actual_size > 0:
            recognized_images += 1
        else:
            unrecognized_regular_files += 1
        entries.append({
            'relative_path': name,
            'size': actual_size,
            'mime': mime,
            'sha256': digest.hexdigest(),
        })
    entries.sort(key=lambda item: item['relative_path'])
    return {
        'sample': sample,
        'expected_images': expected,
        'regular_files': regular_files,
        'recognized_images': recognized_images,
        'unrecognized_regular_files': unrecognized_regular_files,
        'zero_byte_files': zero_byte_files,
        'partial_temp_files': partial_temp_files,
        'symlinks': symlinks,
        'subdirectories': subdirectories,
        'other_entries': other_entries,
        'total_bytes': total_bytes,
        'errors': errors,
        'entries': entries,
    }


def canonical(item):
    return [
        (entry['relative_path'], entry['size'], entry['mime'], entry['sha256'])
        for entry in item['entries']
    ]


def main():
    if len(sys.argv) != 5:
        print('usage: canonical-audit.py DEST OUT_DIR EXPECTED INTERVAL', file=sys.stderr)
        return 2
    destination, out_dir, expected_text, interval_text = sys.argv[1:]
    expected = int(expected_text)
    interval = float(interval_text)
    os.makedirs(out_dir, exist_ok=True)
    samples = []
    for sample in range(1, 4):
        item = inventory(destination, expected, sample)
        samples.append(item)
        with open(os.path.join(out_dir, f'inventory-{sample}.json'), 'w', encoding='utf-8') as handle:
            json.dump(item, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write('\n')
        if sample != 3:
            time.sleep(interval)
    filesystem_pass = all(
        item['regular_files'] == expected
        and item['recognized_images'] == expected
        and item['unrecognized_regular_files'] == 0
        and item['zero_byte_files'] == 0
        and item['partial_temp_files'] == 0
        and item['symlinks'] == 0
        and item['subdirectories'] == 0
        and item['other_entries'] == 0
        and not item['errors']
        for item in samples
    )
    stable_inventory = (
        all(canonical(item) == canonical(samples[0]) for item in samples[1:])
        and all(item['total_bytes'] == samples[0]['total_bytes'] for item in samples[1:])
    )
    result = {
        'destination': os.path.abspath(destination),
        'expected_images': expected,
        'filesystem_pass': filesystem_pass,
        'stable_inventory': stable_inventory,
        'samples': [
            {key: value for key, value in item.items() if key != 'entries'}
            for item in samples
        ],
        'canonical_entry_count': len(samples[0]['entries']),
        'canonical_total_bytes': samples[0]['total_bytes'],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if filesystem_pass and stable_inventory else 4


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
