"""Observable file/geometry regression checks, with synthetic temporary images."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills' / 'tesla-skin-generator' / 'scripts' / 'validate_skin.py'
spec = importlib.util.spec_from_file_location('validate_skin', SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class SkinValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'test-v01.png'
        with Image.open(validator.DEFAULT_TEMPLATE) as template:
            self.image = Image.new('RGBA', template.size, (255, 245, 222, 255))
            self.image.putalpha(template.getchannel('A'))

    def check(self):
        return validator.check_skin(self.path)

    def test_valid_exact_template_alpha(self):
        self.image.save(self.path)
        result = self.check()
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['metrics']['outside_pixels'], 0)
        self.assertEqual(result['metrics']['missing_body_pixels'], 0)

    def test_wrong_dimensions(self):
        self.image.resize((512, 512)).save(self.path)
        self.assertTrue(any('dimensions:' in e for e in self.check()['errors']))

    def test_oversize_valid_png(self):
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('test', 'a' * 1_000_001, zip=False)
        self.image.save(self.path, pnginfo=metadata)
        self.assertTrue(any('file_size:' in e for e in self.check()['errors']))

    def test_opaque_background(self):
        self.image.putalpha(255)
        self.image.save(self.path)
        self.assertTrue(any('transparency:' in e for e in self.check()['errors']))

    def test_empty_transparent_image(self):
        Image.new('RGBA', (1024, 1024)).save(self.path)
        self.assertTrue(any('coverage:' in e for e in self.check()['errors']))

    def test_artwork_in_central_hole(self):
        self.image.paste((255, 150, 50, 255), (450, 450, 550, 550))
        self.image.save(self.path)
        result = self.check()
        self.assertFalse(result['ok'])
        self.assertGreaterEqual(result['metrics']['outside_pixels'], 10_000)

    def test_missing_small_island(self):
        self.image.paste((0, 0, 0, 0), (215, 400, 301, 452))
        self.image.save(self.path)
        self.assertTrue(any('coverage:' in e for e in self.check()['errors']))

    def test_jpeg_disguised_as_png(self):
        self.image.convert('RGB').save(self.path, format='JPEG')
        self.assertTrue(any('format:' in e for e in self.check()['errors']))

    def test_corrupt_file(self):
        self.path.write_bytes(b'not a png')
        self.assertTrue(any('read:' in e for e in self.check()['errors']))

    def test_filename(self):
        self.path = self.path.with_name('invalid@name.png')
        self.image.save(self.path)
        self.assertTrue(any('filename:' in e for e in self.check()['errors']))

    def test_cli_report_and_exit_status(self):
        self.image.save(self.path)
        report = self.path.with_suffix('.validation.json')
        run = subprocess.run([sys.executable, str(SCRIPT), str(self.path), '--report', str(report)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(report.exists())
        run = subprocess.run([sys.executable, str(SCRIPT), str(self.path), '--report', str(report)], capture_output=True)
        self.assertEqual(run.returncode, 2)  # Never overwrite a previous result.


if __name__ == '__main__':
    unittest.main()
