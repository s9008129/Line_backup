"""Deterministic offline proof for the live SCK sidecar requirement (no GUI, no state writes).

Runs observations._support against a scratch root that is shaped like the live project
(under harness-development/, no '/fixtures/'), so the live provider branch is exercised:

  V1  sidecar provider FIXTURE_ONLY, fixture=true  -> must be refused.
  V2  sidecar provider SCREEN_CAPTURE_KIT, fixture=false, internally consistent
      synthetic values -> accepted by the Python validator, demonstrating that the
      Python live branch checks shape/consistency, not the producer's provenance.

Conclusion recorded for the E2E report: every live observation frame needs a
SCREEN_CAPTURE_KIT sidecar; the only producer that emits one (rev28ctl album-support)
requires an open menu with a unique OCR row for the Save All item.
"""
import datetime as dt
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

SCRATCH = Path(__file__).resolve().parents[1] / 'tmp' / 'live-branch-proof'
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))

from line_backup_acceptance.common import AcceptanceError  # noqa: E402
from line_backup_acceptance.project_binding import ProjectReader  # noqa: E402
from line_backup_batch import observations  # noqa: E402


def png(width=16, height=16, marker=7):
    def chunk(name, raw):
        return struct.pack('>I', len(raw)) + name + raw + struct.pack('>I', zlib.crc32(name + raw) & 0xFFFFFFFF)
    rows = b''.join(b'\0' + bytes([marker, 30, 90]) * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(name, raw):
    path = 'harness-development/' + name
    target = SCRATCH / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {'path': path, 'bytes': len(raw), 'sha256': sha(raw)}


def sidecar(frame_id, sck_ref, ocr_ref, *, provider, fixture):
    return {
        'version': 1, 'provider': provider, 'fixture': fixture, 'frame_id': frame_id,
        'session_id': 'execution-sim', 'pid': 4242, 'window_id': 7, 'layout_key': 'layout-sim',
        'captured_at': NOW, 'sck_frame': sck_ref, 'ocr': ocr_ref,
        'native_binding': {
            'bundle_id': 'jp.naver.line.mac', 'pid': 4242, 'window_id': 7, 'display_id': 1,
            'cua_capture_bounds_points': [0, 0, 16, 16], 'sck_window_bounds_points': [0, 0, 16, 16],
            'display_bounds_points': [0, 0, 16, 16], 'cua_size_px': [16, 16], 'sck_size_px': [16, 16],
        },
        'uncertainty_px': 2, 'safe_margin_px': 6, 'interactive_intersection_px': [0, 0, 16, 16],
    }


NOW = dt.datetime.now(dt.timezone.utc).isoformat()
SCRATCH.mkdir(parents=True, exist_ok=True)

frame = ref('frame.png', png(marker=11))
sck = ref('sck.png', png(marker=77))
anchors = [['anchor-a', 2, 2], ['anchor-b', 12, 2], ['anchor-c', 2, 12]]
ocr_items = [{'text': text, 'confidence': 0.99, 'candidate_count': 1, 'bounds': [x, y, 2, 2]}
             for text, x, y in anchors]
ocr = ref('ocr.json', json.dumps({
    'version': 1, 'cua_frame_id': frame['sha256'], 'sck_frame_sha256': sck['sha256'],
    'cua': ocr_items, 'sck': ocr_items,
}).encode())

record = {
    'frame_id': frame['sha256'], 'session_id': 'execution-sim', 'pid': 4242, 'window_id': 7,
    'layout_key': 'layout-sim', 'captured_at': NOW, 'width': 16, 'height': 16, 'frame': frame,
}
cfg = {'app_identifier': 'jp.naver.line.mac'}

results = {}
for name, variant in (
        ('v1_fixture_only_sidecar', {'provider': 'FIXTURE_ONLY', 'fixture': True}),
        ('v2_screen_capture_kit_sidecar', {'provider': 'SCREEN_CAPTURE_KIT', 'fixture': False})):
    value = sidecar(frame['sha256'], sck, ocr, **variant)
    raw = json.dumps(value, ensure_ascii=False).encode()
    sidecar_ref = ref(name + '.json', raw)
    reader = ProjectReader(str(SCRATCH))
    try:
        observations._support(reader, sidecar_ref, record, cfg, now=dt.datetime.now(dt.timezone.utc), max_age=None)
        results[name] = {'outcome': 'ACCEPTED', 'sidecar_sha256': sidecar_ref['sha256']}
    except AcceptanceError as exc:
        results[name] = {'outcome': 'REFUSED', 'code': exc.code, 'message': str(exc),
                         'sidecar_sha256': sidecar_ref['sha256']}
    finally:
        reader.close()

print(json.dumps({'proof': 'live-branch SCK sidecar requirement', 'scratch_root': str(SCRATCH.relative_to(Path(__file__).resolve().parents[3])),
                  'results': results}, ensure_ascii=False, indent=2))
