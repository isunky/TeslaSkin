#!/usr/bin/env python3
"""Read-only Model Y skin checks. Requires Python 3 and Pillow.

Exit 0: file/geometry checks pass (visual and in-car review still required).
Exit 1: invalid/unreadable skin or template. Exit 2: CLI/dependency error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    print('Missing Pillow. Install in the selected Python environment: python -m pip install Pillow', file=sys.stderr)
    raise SystemExit(2)

SIZE = (1024, 1024)
MAX_BYTES = 1_000_000
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / 'assets' / 'template.png'
# Negligible antialiasing differences only; large shape errors must fail.
MAX_OUTSIDE_PIXELS = 256
MAX_MISSING_PIXELS = 256
ALPHA_VISIBLE = 16


def check_skin(path, template=DEFAULT_TEMPLATE):
    path, template = Path(path), Path(template)
    result = {'ok': False, 'file': str(path.resolve()), 'errors': [],
              'warnings': ['File checks do not verify artwork direction, seams or in-car appearance.'],
              'metrics': {}, 'checks': {'file': 'pending', 'geometry': 'pending', 'edge': 'pending',
                                       'artwork_direction': 'manual_required', 'app_front': 'pending',
                                       'app_side': 'pending', 'app_rear': 'pending', 'vehicle': 'pending'}}
    errors, metrics = result['errors'], result['metrics']
    if not re.fullmatch(r'[A-Za-z0-9 _-]+\.[Pp][Nn][Gg]', path.name) or len(path.name) > 30:
        errors.append('filename: use .png and ASCII letters/digits/spaces/_/-, max 30 characters including extension')
    try:
        metrics['bytes'] = path.stat().st_size
        if metrics['bytes'] > MAX_BYTES:
            errors.append(f'file_size: {metrics["bytes"]} bytes exceeds {MAX_BYTES}')
        with Image.open(path) as source:
            metrics['format'] = source.format
            metrics['size'] = list(source.size)
            if source.format != 'PNG':
                errors.append('format: file content is not PNG')
            if getattr(source, 'n_frames', 1) != 1:
                errors.append('format: animated PNG is not supported')
            if source.size != SIZE:
                errors.append(f'dimensions: expected {SIZE[0]}x{SIZE[1]}')
            source.load()  # Check full decoding, including truncated pixel data.
            skin = source.convert('RGBA')
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        errors.append(f'read: {exc}')
        return result

    try:
        with Image.open(template) as source:
            source.load()
            if source.format != 'PNG' or source.size != SIZE:
                raise ValueError('template must be a 1024x1024 PNG')
            baseline = source.convert('RGBA')
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        errors.append(f'template: {exc}')
        return result

    alpha = skin.getchannel('A')
    expected_alpha = baseline.getchannel('A')
    if skin.size != SIZE:
        # Still diagnose exported fringe at native resolution; do not claim UV fit.
        metrics['diagnostic_only'] = True
        baseline = baseline.resize(skin.size, Image.Resampling.NEAREST)
        expected_alpha = baseline.getchannel('A')
        result['warnings'].append('Geometry metrics use a scaled template for diagnosis only; wrong dimensions remain a failure.')
    expected_visible = expected_alpha.point(lambda p: 255 if p >= ALPHA_VISIBLE else 0)
    allowed_count = expected_visible.histogram()[255]
    if allowed_count == 0 or allowed_count == SIZE[0] * SIZE[1]:
        errors.append('template: expected both body islands and transparent gaps')
        return result
    visible = alpha.point(lambda p: 255 if p >= ALPHA_VISIBLE else 0)
    outside = ImageChops.multiply(visible, ImageChops.invert(expected_visible))
    metrics['outside_pixels'] = outside.histogram()[255]
    if metrics['outside_pixels'] > MAX_OUTSIDE_PIXELS:
        errors.append(f'transparency: {metrics["outside_pixels"]} visible pixels outside template (max {MAX_OUTSIDE_PIXELS})')

    # Faint stray alpha (<16) was invisible to the old threshold and can still
    # produce colored seams in texture sampling. Check all nonzero alpha outside.
    absent = expected_alpha.point(lambda p: 255 if p == 0 else 0)
    stray = ImageChops.multiply(alpha.point(lambda p: 255 if p > 0 else 0), absent)
    metrics['stray_alpha_pixels'] = stray.histogram()[255]
    if metrics['stray_alpha_pixels'] > MAX_OUTSIDE_PIXELS:
        errors.append(f'edge: {metrics["stray_alpha_pixels"]} nonzero-alpha pixels in fully transparent template gaps')
    result['checks']['edge'] = 'failed' if metrics['stray_alpha_pixels'] > MAX_OUTSIDE_PIXELS else 'passed'

    # Opaque paint interiors must stay opaque; transparent white padding is not paint.
    red, green, blue, _ = baseline.split()
    bright = ImageChops.darker(ImageChops.darker(red, green), blue).point(lambda p: 255 if p >= 240 else 0)
    opaque = expected_alpha.point(lambda p: 255 if p >= 250 else 0)
    required = ImageChops.multiply(bright, opaque)
    missing = ImageChops.multiply(required, alpha.point(lambda p: 255 if p < 250 else 0))
    metrics['missing_body_pixels'] = missing.histogram()[255]
    metrics['required_body_pixels'] = required.histogram()[255]
    metrics['alpha_extrema'] = list(alpha.getextrema())
    if metrics['required_body_pixels'] == 0:
        errors.append('template: no opaque white paint islands found')
    if metrics['missing_body_pixels'] > MAX_MISSING_PIXELS:
        errors.append(f'coverage: {metrics["missing_body_pixels"]} body pixels not opaque (max {MAX_MISSING_PIXELS})')
    if alpha.getextrema()[0] != 0:
        errors.append('transparency: expected fully transparent gaps')
    if metrics['outside_pixels'] or metrics['missing_body_pixels']:
        result['warnings'].append('Nonzero shape differences: review contour edges even when within the antialias tolerance.')
    geometric_errors = ('dimensions:', 'transparency:', 'coverage:', 'template:')
    result['checks']['geometry'] = 'failed' if any(e.startswith(geometric_errors) for e in errors) else 'passed'
    result['checks']['file'] = 'failed' if any(e.startswith(('file_size:', 'filename:', 'format:', 'dimensions:')) for e in errors) else 'passed'
    result['ok'] = not errors
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--template', type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument('--report', type=Path, help='Optional JSON report; never overwrites an existing file')
    args = parser.parse_args()
    if args.report and (args.report.resolve() == args.image.resolve() or args.report.resolve() == args.template.resolve()):
        parser.error('report must not replace the image or template')
    result = check_skin(args.image, args.template)
    payload = json.dumps(result, ensure_ascii=True, indent=2)
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open('x', encoding='utf-8') as target:
                target.write(payload + '\n')
        except OSError as exc:
            print(f'Cannot save report: {exc}', file=sys.stderr)
            return 2
    print(payload)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
