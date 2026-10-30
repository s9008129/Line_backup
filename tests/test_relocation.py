import json
import shutil
import tempfile
import unittest
from pathlib import Path
from line_backup_batch.daily import CORE_ROOT, DailyRecords, DailyError, exclusive_rename
from line_backup_batch.relocation import prepare


class RelocationTests(unittest.TestCase):
    def test_different_copies_are_rejected_before_any_receipt(self):
        with tempfile.TemporaryDirectory(prefix='.line-daily-tests-', dir=CORE_ROOT) as tmp:
            base = Path(tmp)
            source, current = base / 'old', base / 'copy'
            source.mkdir()
            (source / 'photo.png').write_bytes(b'synthetic original')
            shutil.copytree(source, current)
            (current / 'photo.png').write_bytes(b'synthetic changed')
            with self.assertRaisesRegex(DailyError, 'RELOCATION_COPIES_DIFFER'):
                prepare(source, current, CORE_ROOT / (base.name + '-destination'), base / 'receipt')
            self.assertFalse((base / 'receipt').exists())
            self.assertEqual((source / 'photo.png').read_bytes(), b'synthetic original')

    def test_receipt_preserves_records_and_rejects_drift(self):
        with tempfile.TemporaryDirectory(prefix='.line-daily-tests-', dir=CORE_ROOT) as tmp:
            base = Path(tmp)
            source = base / 'old'
            current = base / 'copy'
            source.mkdir()
            evidence = base / 'source.json'
            evidence.write_text('{"synthetic": true}')
            original = DailyRecords(source)
            original.initialize(binding_evidence=evidence, history_scope_evidence=evidence)
            original.bind(session_id='old-session', local_group_id=original.memory()['local_group_id'],
                          observation=evidence, handoff=evidence)
            shutil.copytree(source, current)
            # prepare requires the final backup root directly under this project.
            destination = CORE_ROOT / (base.name + '-destination')
            try:
                raw = (current / 'backup-records/group.json').read_bytes()
                receipt = prepare(source, current, destination, base / 'receipt')
                exclusive_rename(current, destination)
                store = DailyRecords(destination)
                self.assertEqual(store.memory()['albums'], [])
                self.assertEqual((destination / 'backup-records/group.json').read_bytes(), raw)
                with self.assertRaisesRegex(DailyError, 'FRESH_FOREGROUND'):
                    with store.locked():
                        store.bound('old-session')
                store.bind(session_id='synthetic-new-session',
                           local_group_id=store.memory()['local_group_id'],
                           observation=evidence, handoff=evidence)
                with store.locked():
                    store.bound('synthetic-new-session')
                self.assertEqual(DailyRecords(destination).memory()['albums'], [])
                receipt_path = destination / 'backup-records/relocation.json'
                receipt_raw = receipt_path.read_bytes()
                receipt_path.write_bytes(receipt_raw + b' ')
                with self.assertRaisesRegex(DailyError, 'RELOCATION_RECEIPT_CHANGED'):
                    store.memory()
                receipt_path.write_bytes(receipt_raw)
                path = destination / 'backup-records/group.json'
                path.write_bytes(raw + b' ')
                with self.assertRaisesRegex(DailyError, 'RELOCATION_BINDING_CHANGED'):
                    store.memory()
            finally:
                if destination.exists():
                    shutil.rmtree(destination)


if __name__ == '__main__':
    unittest.main()
