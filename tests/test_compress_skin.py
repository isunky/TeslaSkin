"""Compression must preserve geometry and alpha, and never overwrite artwork."""
import importlib.util
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/tesla-skin-generator/scripts/compress_skin.py'
spec = importlib.util.spec_from_file_location('compress_skin', SCRIPT)
compressor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compressor)


class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'original.png'
        self.output = Path(self.tmp.name) / 'compressed.png'
        self.image = Image.new('RGBA', (128, 128), (250, 225, 190, 255))
        self.image.putalpha(Image.frombytes('L', self.image.size, bytes(range(256)) * 64))

    def test_under_limit_copies_original_bytes(self):
        self.image.save(self.source)
        before = self.source.read_bytes()
        result = compressor.compress_png(self.source, self.output)
        self.assertEqual(result['method'], 'unchanged')
        self.assertEqual(self.output.read_bytes(), before)
        self.assertEqual(self.source.read_bytes(), before)

    def test_lossless_removes_metadata_preserves_pixels_and_color_profile(self):
        info = PngImagePlugin.PngInfo()
        info.add_text('padding', 'x' * 1_000_001)
        info.add(b'gAMA', (45455).to_bytes(4, 'big'))
        self.image.save(self.source, pnginfo=info, icc_profile=b'test-profile')
        result = compressor.compress_png(self.source, self.output)
        self.assertEqual(result['method'], 'lossless')
        self.assertLessEqual(result['output_bytes'], 1_000_000)
        with Image.open(self.output) as image:
            self.assertEqual(image.convert('RGBA').tobytes(), self.image.tobytes())
            self.assertEqual(image.info['icc_profile'], b'test-profile')
            self.assertAlmostEqual(image.info['gamma'], .45455)

    def test_quantization_preserves_all_alpha_values_and_dimensions(self):
        rng = random.Random(42)
        image = Image.frombytes('RGB', (512, 512), rng.randbytes(512 * 512 * 3)).convert('RGBA')
        alpha = Image.frombytes('L', image.size, bytes(range(256)) * 1024)
        image.putalpha(alpha)
        image.save(self.source)
        result = compressor.compress_png(self.source, self.output, max_bytes=750_000)
        self.assertTrue(result['lossy_rgb'])
        self.assertLessEqual(result['output_bytes'], 750_000)
        with Image.open(self.output) as output:
            self.assertEqual(output.size, image.size)
            self.assertEqual(output.getchannel('A').tobytes(), alpha.tobytes())

    def test_unreachable_limit_leaves_no_output(self):
        self.image.save(self.source)
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, 'cannot fit'):
            compressor.compress_png(self.source, self.output, max_bytes=10)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_no_overwrite(self):
        self.image.save(self.source)
        with self.assertRaisesRegex(ValueError, 'differ'):
            compressor.compress_png(self.source, self.source)
        self.output.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            compressor.compress_png(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), b'existing')

    def test_rejects_non_png(self):
        self.image.convert('RGB').save(self.source, format='JPEG')
        with self.assertRaisesRegex(ValueError, 'single-frame PNG'):
            compressor.compress_png(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_report_and_size_failure_are_distinct(self):
        self.image.save(self.source)
        report = self.output.with_suffix('.compression.json')
        run = subprocess.run([sys.executable, str(SCRIPT), str(self.source), str(self.output),
                              '--report', str(report)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(report.exists())
        run = subprocess.run([sys.executable, str(SCRIPT), str(self.source), str(self.output)], capture_output=True)
        self.assertEqual(run.returncode, 1)


if __name__ == '__main__':
    unittest.main()
