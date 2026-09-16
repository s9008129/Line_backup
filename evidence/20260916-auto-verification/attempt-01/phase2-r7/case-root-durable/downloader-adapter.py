#!/usr/bin/env python3
import argparse, json, time, zlib, struct
p = argparse.ArgumentParser(); p.add_argument('--counter'); p.add_argument('--outcome')
p.add_argument('--crash-after-dispatch', action='store_true')
n = p.parse_args()
with open(n.counter, 'a', encoding='utf-8') as fh:
    fh.write(json.dumps({'outcome': n.outcome, 'at': time.time()}) + '\n')
dest = '/private/tmp/line-backup-acceptance-case-09/backups/album-integration'
files = 57
import os
os.makedirs(dest, exist_ok=True)
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
raw = b''.join(b'\x00' + bytes((10, 20, 30) * 8) for _ in range(8))
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
for i in range(files):
    with open(os.path.join(dest, f'image-{i:03d}.png'), 'wb') as fh:
        fh.write(png)
raise SystemExit(1 if n.crash_after_dispatch else 0)
