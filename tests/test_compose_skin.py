"""UV assembly invariants and observable orientation/safe-area behavior."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/tesla-skin-generator/scripts/compose_skin.py'
spec = importlib.util.spec_from_file_location('compose_skin', SCRIPT)
composer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composer)


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template, cls.parts, cls.masks = composer.template_parts()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.design = self.root / 'design.json'
        self.output = self.root / 'skin.png'

    def write_design(self, parts=None):
        self.design.write_text(json.dumps({'base_color': '#fff2df', 'parts': parts or {}}), encoding='utf-8')

    def test_all_sixteen_islands_are_distinct(self):
        self.assertEqual(len(self.masks), 16)
        union = Image.new('L', self.template.size)
        for mask in self.masks.values():
            self.assertIsNotNone(mask.getbbox())
            self.assertIsNone(ImageChops.multiply(mask, union).getbbox())
            union = ImageChops.lighter(union, mask)

    def test_export_exact_alpha_and_no_template_guide_ink(self):
        self.write_design()
        report = composer.compose(self.design, self.output)
        with Image.open(self.output) as output:
            self.assertEqual(output.size, (1024, 1024))
            self.assertEqual(output.getchannel('A').tobytes(), self.template.getchannel('A').tobytes())
            # Every RGB pixel, including old black guide lines, is body color.
            self.assertEqual(output.convert('RGB').getextrema(), ((255, 255), (242, 242), (223, 223)))
        self.assertEqual(report['checks']['app_front'], 'pending')
        self.assertEqual(report['checks']['vehicle'], 'pending')

    def test_actual_motif_orientation_hood_and_both_doors(self):
        motif = Image.new('RGBA', (30, 60))
        draw = ImageDraw.Draw(motif)
        draw.rectangle((8, 0, 21, 18), fill=(230, 10, 10, 255))
        draw.rectangle((8, 41, 21, 59), fill=(10, 10, 230, 255))
        mask = Image.new('L', (120, 120), 255)
        for name in ('hood', 'left_front_door', 'right_front_door'):
            canvas = Image.new('RGBA', mask.size)
            part = {'rotation_cw': self.parts[name]['rotation_cw'], 'inset': 4}
            composer.place_layer(canvas, motif, mask, part, {'scale': .65})
            red, blue = [], []
            for y in range(canvas.height):
                for x in range(canvas.width):
                    r, g, b, a = canvas.getpixel((x, y))
                    if a > 200 and r > 180 and b < 60: red.append((x, y))
                    if a > 200 and b > 180 and r < 60: blue.append((x, y))
            rc = [sum(p[i] for p in red)/len(red) for i in (0, 1)]
            bc = [sum(p[i] for p in blue)/len(blue) for i in (0, 1)]
            if name == 'hood': self.assertGreater(rc[1], bc[1])
            elif name.startswith('left'): self.assertGreater(rc[0], bc[0])
            else: self.assertLess(rc[0], bc[0])

    def test_motif_has_no_clipped_pixels_outside_safe_area(self):
        mask = Image.new('L', (120, 120))
        ImageDraw.Draw(mask).polygon([(60, 8), (112, 110), (8, 110)], fill=255)
        canvas = Image.new('RGBA', mask.size)
        motif = Image.new('RGBA', (70, 50), (200, 100, 40, 255))
        report = composer.place_layer(canvas, motif, mask, {'inset': 4, 'rotation_cw': 0},
                                      {'scale': 1, 'center': [.5, .65]})
        safe = mask.filter(composer.ImageFilter.MinFilter(9))
        self.assertIsNone(ImageChops.multiply(canvas.getchannel('A'), ImageChops.invert(safe)).getbbox())
        self.assertEqual(report['clipped_pixels'], 0)

    def test_cleanup_removes_faint_magenta_and_disconnected_noise(self):
        image = Image.new('RGBA', (100, 100))
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, 80, 80), fill=(220, 130, 50, 255))
        draw.rectangle((0, 0, 18, 15), fill=(255, 0, 255, 8))
        draw.point((99, 99), fill=(255, 0, 255, 255))
        path = self.root / 'motif.png'; image.save(path)
        clean = composer.clean_motif(path)
        self.assertEqual(clean.size, (61, 61))
        self.assertEqual(clean.getpixel((0, 0)), (220, 130, 50, 255))

    def test_rejects_flat_background_art(self):
        path = self.root / 'opaque.png'
        Image.new('RGBA', (80, 80), 'white').save(path)
        with self.assertRaisesRegex(ValueError, 'real transparency'):
            composer.clean_motif(path)

    def test_no_overwrite_or_unknown_parts(self):
        self.write_design({'not_a_model_y_part': []})
        with self.assertRaisesRegex(ValueError, 'known Model Y'):
            composer.compose(self.design, self.output)
        self.assertFalse(self.output.exists())
        self.write_design()
        self.output.write_bytes(b'existing')
        with self.assertRaises(FileExistsError): composer.compose(self.design, self.output)
        self.assertEqual(self.output.read_bytes(), b'existing')

    def test_changing_hood_does_not_change_other_parts(self):
        image = Image.new('RGBA', (60, 60))
        ImageDraw.Draw(image).ellipse((5, 5, 55, 55), fill=(210, 90, 30, 255))
        image.save(self.root / 'motif.png')
        self.write_design({'left_front_door': [{'image': 'motif.png'}]})
        composer.compose(self.design, self.output)
        before = Image.open(self.output).convert('RGBA')
        self.write_design({'left_front_door': [{'image': 'motif.png'}], 'hood': [{'image': 'motif.png'}]})
        second = self.root / 'second.png'
        composer.compose(self.design, second)
        with Image.open(second) as after:
            diff = ImageChops.difference(before.convert('RGB'), after.convert('RGB'))
            outside = ImageChops.multiply(diff.convert('L'), ImageChops.invert(self.masks['hood']))
            self.assertIsNone(outside.getbbox())


if __name__ == '__main__':
    unittest.main()
