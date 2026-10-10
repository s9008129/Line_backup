import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,os.environ['LINE_BACKUP_BATCH_TASK'])
from fixture_support import Fixture,png
from line_backup_batch.content import verify
from line_backup_acceptance.common import AcceptanceError

class ContentTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture();self.path=self.f.root/'backups/new';self.path.mkdir();self.now=0
    def tearDown(self):self.f.close()
    def wait(self,seconds):self.now+=seconds
    def verify(self,n,**kwargs):
        return verify(str(self.f.root),str(self.path),n,self.f.cfg,self.f.binding['binary_path'],self.f.binding['binary_sha256'],
            clock=lambda:self.now,sleep=self.wait,**kwargs)
    def images(self,n):
        for i in range(n):(self.path/f'{i}.png').write_bytes(png(4,4,i))
    def test_actual_full_rgb_decoder_dynamic_counts_and_measured_bytes(self):
        for n in (2,3):
            with self.subTest(count=n):
                for p in self.path.iterdir():p.unlink()
                self.images(n);v,proof=self.verify(n)
                self.assertEqual(v['image_files'],n);self.assertEqual(v['stable_samples'],3)
                self.assertEqual(v['total_bytes'],sum(p.stat().st_size for p in self.path.iterdir()))
                self.assertTrue(all(r['decoded'] for r in proof['decoder']['entries']))
                self.assertEqual([s['monotonic'] for s in proof['samples']],list(range(int(self.now)-2,int(self.now)+1)))
    def test_pause_missing_count_never_passes_stability_alone(self):
        self.images(1)
        with self.assertRaisesRegex(AcceptanceError,'DOWNLOAD_TIMEOUT'):self.verify(2)
    def test_extra_hidden_directory_symlink_zero_and_temp_refuse(self):
        builders=[lambda:(self.path/'extra.png').write_bytes(png(4,4)),lambda:(self.path/'.hidden').write_bytes(b'x'),
            lambda:(self.path/'folder').mkdir(),lambda:(self.path/'link').symlink_to(self.f.root/'state/backup_state.json'),
            lambda:(self.path/'zero.png').touch(),lambda:(self.path/'a.part').write_bytes(b'x')]
        for build in builders:
            for p in self.path.iterdir():
                p.rmdir() if p.is_dir() and not p.is_symlink() else p.unlink()
            self.images(1);build();self.now=0
            with self.subTest(build=build),self.assertRaises(AcceptanceError):self.verify(1)
    def test_truncated_png_actual_pixel_decoder_rejects(self):
        (self.path/'bad.png').write_bytes(png(4,4)[:40])
        with self.assertRaisesRegex(AcceptanceError,'PIXEL_DECODE_FAILED'):self.verify(1)
    def test_content_mutation_after_decode_refuses(self):
        self.images(1)
        with self.assertRaisesRegex(AcceptanceError,'DOWNLOAD_CHANGED_AFTER_DECODE'):
            self.verify(1,after_decode=lambda:(self.path/'0.png').write_bytes(png(4,4,77)))
    def test_interval_cannot_be_faked_by_non_advancing_clock(self):
        self.images(1)
        with self.assertRaisesRegex(AcceptanceError,'STABILITY_INTERVAL'):
            verify(str(self.f.root),str(self.path),1,self.f.cfg,self.f.binding['binary_path'],self.f.binding['binary_sha256'],
                clock=lambda:0,sleep=lambda seconds:None)
