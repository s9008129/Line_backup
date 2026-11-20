import base64
import hashlib
from subprocess import CompletedProcess, TimeoutExpired
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from line_backup_batch import download_check
from line_backup_batch.download_check import (
    DownloadCheckError,
    classify,
    validate,
)


# A small, valid 1x1 PNG fixture. It is generated in the test directory only.
PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO'
    '+nmAAAAABJRU5ErkJggg==')


class DownloadSignatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_classifies_magic_png_and_hashes_tool_output(self):
        path = self.root / 'sample.png'
        path.write_bytes(PNG_1X1)

        result = classify(path)

        self.assertEqual(result['schema'], 'line-notes-file-signature/v1')
        self.assertEqual(result['kind'], 'PHOTO')
        self.assertEqual(result['mime_type'], 'image/png')
        self.assertRegex(result['tool_sha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(result['stdout_sha256'],
                         hashlib.sha256(b'image/png\n').hexdigest())
        self.assertIs(validate(result, path.name), result)

    def test_classifies_text_disguised_as_png_as_nonmedia(self):
        path = self.root / 'not-really.png'
        path.write_text('ordinary text, not an image', encoding='utf-8')

        result = classify(path)
        self.assertEqual(result['kind'], 'NON_MEDIA')
        self.assertEqual(result['mime_type'], 'text/plain')

    def test_classifies_pdf_as_nonmedia(self):
        path = self.root / 'document.pdf'
        path.write_bytes(b'%PDF-1.4')
        result = classify(path)
        self.assertEqual(result['kind'], 'NON_MEDIA')
        self.assertEqual(result['mime_type'], 'application/pdf')

    def test_rejects_png_magic_with_jpeg_suffix(self):
        path = self.root / 'png-disguised-as.jpg'
        path.write_bytes(PNG_1X1)

        with self.assertRaisesRegex(DownloadCheckError,
                                    '^MEDIA_SIGNATURE_SUFFIX_MISMATCH$'):
            classify(path)

    def test_classifies_nonmedia_text_with_unsupported_suffix(self):
        path = self.root / 'readme.unknown'
        path.write_text('ordinary text', encoding='utf-8')

        result = classify(path)

        self.assertEqual(result['kind'], 'NON_MEDIA')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertIs(validate(result, path.name), result)

    def test_rejects_unknown_mime_instead_of_classifying_as_nonmedia(self):
        path = self.root / 'opaque.unknown'
        path.write_bytes(bytes(range(256)))

        with self.assertRaisesRegex(DownloadCheckError,
                                    '^UNSUPPORTED_MEDIA_MIME$'):
            classify(path)

    def test_validate_limits_nonmedia_to_explicit_mimes(self):
        result = {
            'schema': 'line-notes-file-signature/v1',
            'kind': 'NON_MEDIA',
            'mime_type': 'application/octet-stream',
            'tool_sha256': 'a' * 64,
            'stdout_sha256': hashlib.sha256(
                b'application/octet-stream\n').hexdigest(),
        }
        with self.assertRaisesRegex(DownloadCheckError,
                                    '^INVALID_SIGNATURE_METADATA$'):
            validate(result, 'payload.bin')

    def test_validate_rejects_forged_metadata(self):
        valid = {
            'schema': 'line-notes-file-signature/v1',
            'kind': 'PHOTO',
            'mime_type': 'image/png',
            'tool_sha256': 'a' * 64,
            'stdout_sha256': hashlib.sha256(b'image/png\n').hexdigest(),
        }
        cases = []
        wrong_schema = dict(valid, schema='forged/v1')
        cases.append(wrong_schema)
        bad_hash = dict(valid, tool_sha256='not-a-hash')
        cases.append(bad_hash)
        wrong_kind = dict(valid, kind='VIDEO')
        wrong_mime = dict(valid, mime_type='image/jpeg',
                          stdout_sha256=hashlib.sha256(
                              b'image/jpeg\n').hexdigest())
        extra_field = dict(valid, trusted=True)
        cases.append(extra_field)

        for forged in cases:
            with self.subTest(forged=forged):
                with self.assertRaisesRegex(DownloadCheckError,
                                            '^INVALID_SIGNATURE_METADATA$'):
                    validate(forged, 'sample.png')

        for forged in (wrong_kind, wrong_mime):
            with self.subTest(forged=forged):
                with self.assertRaisesRegex(
                        DownloadCheckError,
                        '^MEDIA_SIGNATURE_SUFFIX_MISMATCH$'):
                    validate(forged, 'sample.png')

    def test_validate_rejects_kind_or_mime_suffix_mismatch(self):
        result = {
            'schema': 'line-notes-file-signature/v1',
            'kind': 'VIDEO',
            'mime_type': 'video/mp4',
            'tool_sha256': 'a' * 64,
            'stdout_sha256': hashlib.sha256(b'video/mp4\n').hexdigest(),
        }
        with self.assertRaisesRegex(DownloadCheckError,
                                    '^MEDIA_SIGNATURE_SUFFIX_MISMATCH$'):
            validate(result, 'sample.png')

    def test_validate_rejects_stdout_hash_mismatch(self):
        result = {
            'schema': 'line-notes-file-signature/v1',
            'kind': 'PHOTO',
            'mime_type': 'image/png',
            'tool_sha256': 'a' * 64,
            'stdout_sha256': 'b' * 64,
        }
        with self.assertRaisesRegex(DownloadCheckError,
                                    '^INVALID_SIGNATURE_METADATA$'):
            validate(result, 'sample.png')

    def _mock_file_result(self, path, *, returncode=0, stdout=b'image/png\n',
                          stderr=b''):
        path.write_bytes(PNG_1X1)
        return CompletedProcess([], returncode, stdout, stderr)

    def test_rejects_nonzero_file_tool_exit(self):
        path = self.root / 'sample.png'
        completed = self._mock_file_result(path, returncode=2)
        with mock.patch.object(download_check.subprocess, 'run',
                                return_value=completed):
            with self.assertRaisesRegex(DownloadCheckError,
                                        '^FILE_TOOL_FAILED$'):
                classify(path)

    def test_rejects_file_tool_stderr(self):
        path = self.root / 'sample.png'
        completed = self._mock_file_result(path, stderr=b'warning\n')
        with mock.patch.object(download_check.subprocess, 'run',
                                return_value=completed):
            with self.assertRaisesRegex(DownloadCheckError,
                                        '^FILE_TOOL_STDERR_NOT_EMPTY$'):
                classify(path)

    def test_rejects_file_tool_timeout(self):
        path = self.root / 'sample.png'
        self._mock_file_result(path)
        with mock.patch.object(download_check.subprocess, 'run',
                                side_effect=TimeoutExpired('file', 30)):
            with self.assertRaisesRegex(DownloadCheckError,
                                        '^FILE_TOOL_TIMEOUT$'):
                classify(path)

    def test_rejects_file_tool_drift(self):
        path = self.root / 'sample.png'
        completed = self._mock_file_result(path)
        snapshots = [((1, 2, 3), 'a' * 64), ((1, 2, 3), 'b' * 64)]
        with mock.patch.object(download_check, '_tool_snapshot',
                                side_effect=snapshots), \
                mock.patch.object(download_check.subprocess, 'run',
                                  return_value=completed):
            with self.assertRaisesRegex(DownloadCheckError,
                                        '^FILE_TOOL_CHANGED$'):
                classify(path)


if __name__ == '__main__':
    unittest.main()
