#!/usr/bin/env python3
"""Place upright motif PNGs onto the immutable Model Y UV template.

The JSON design contains base_color, optional shared backgrounds, and
parts: {part_id: [foreground layers]}. Shared prints can flow across a group
of adjacent UV islands; foreground subjects retain strict safety margins.
Layer image paths are relative to the design JSON. Rotation defaults come from
assets/parts.json. Geometry, safety margins and alpha are enforced by code.
"""
import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import sys

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    print('Missing Pillow: python -m pip install Pillow', file=sys.stderr)
    raise SystemExit(2)

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'assets/template.png'
PARTS = SKILL / 'assets/parts.json'


def template_parts():
    config = json.loads(PARTS.read_text(encoding='utf-8'))
    if hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() != config['template_sha256']:
        raise ValueError('template hash differs from the calibrated Model Y template')
    with Image.open(TEMPLATE) as source:
        template = source.convert('RGBA')
    r, g, b, a = template.split()
    bright = ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 255 if v >= 240 else 0)
    labels = ImageChops.multiply(bright, a.point(lambda v: 255 if v >= 250 else 0))
    masks = {}
    for label, (name, part) in enumerate(config['parts'].items(), 1):
        seed = tuple(part['seed'])
        if labels.getpixel(seed) != 255:
            raise ValueError(f'invalid/duplicate part seed: {name}')
        ImageDraw.floodfill(labels, seed, label)
        mask = labels.point(lambda v: 255 if v == label else 0)
        masks[name] = mask
    # Small antialias fragments may remain, but no main island may be omitted.
    if labels.histogram()[255] > 256:
        raise ValueError('unmapped template paint island')
    return template, config['parts'], masks


def clean_motif(path):
    """Remove low-alpha fringe and tiny disconnected artifacts; never redraw art."""
    with Image.open(path) as source:
        if source.format != 'PNG' or getattr(source, 'n_frames', 1) != 1:
            raise ValueError(f'motif must be a single-frame PNG: {path}')
        image = source.convert('RGBA')
    alpha = image.getchannel('A')
    if alpha.getextrema()[0] != 0:
        raise ValueError(f'motif needs real transparency, not a flat background: {path}')
    w, h = image.size
    visible = bytearray(alpha.point(lambda v: 255 if v > 12 else 0).tobytes())
    kept = bytearray(w * h)
    for start, value in enumerate(visible):
        if not value:
            continue
        queue, component = deque([start]), []
        visible[start] = 0
        while queue:
            pos = queue.popleft()
            component.append(pos)
            x, y = pos % w, pos // w
            for nxt in ((pos - 1 if x else -1), (pos + 1 if x + 1 < w else -1),
                        (pos - w if y else -1), (pos + w if y + 1 < h else -1)):
                if nxt >= 0 and visible[nxt]:
                    visible[nxt] = 0
                    queue.append(nxt)
        if len(component) >= 64:
            for pos in component:
                kept[pos] = 255
    filtered = ImageChops.multiply(alpha, Image.frombytes('L', (w, h), bytes(kept)))
    image.putalpha(filtered)
    box = filtered.getbbox()
    if box is None:
        raise ValueError(f'no usable motif remains after fringe cleanup: {path}')
    return image.crop(box)


def number(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{label} must be between {low} and {high}')
    return value


def place_background(canvas, source, masks, spec):
    names = spec.get('parts')
    if not isinstance(names, list) or not names or len(set(names)) != len(names) or any(name not in masks for name in names):
        raise ValueError('background parts must be a nonempty list of unique known part IDs')
    rotation = spec.get('rotation_cw', 0)
    if rotation not in (0, 90, 180, 270):
        raise ValueError('background rotation_cw must be 0/90/180/270')
    mirror = spec.get('mirror', False)
    if not isinstance(mirror, bool):
        raise ValueError('background mirror must be a boolean')
    with Image.open(source) as original:
        if original.format != 'PNG' or getattr(original, 'n_frames', 1) != 1:
            raise ValueError('background artwork must be a single-frame PNG')
        artwork = original.convert('RGBA')
    source_box = spec.get('source_box', [0, 0, 1, 1])
    if not isinstance(source_box, list) or len(source_box) != 4:
        raise ValueError('source_box must be [left, top, right, bottom]')
    u0, v0, u1, v1 = [number(n, 0, 1, 'source_box') for n in source_box]
    if u0 >= u1 or v0 >= v1:
        raise ValueError('source_box must have positive area')
    crop = tuple(round(n * length) for n, length in zip(source_box, (artwork.width, artwork.height) * 2))
    if crop[0] >= crop[2] or crop[1] >= crop[3]:
        raise ValueError('source_box rounds to an empty crop')
    artwork = artwork.crop(crop)
    if mirror:
        artwork = ImageOps.mirror(artwork)
    artwork = artwork.rotate(-rotation, expand=True)
    union, blocked = Image.new('L', canvas.size), Image.new('L', canvas.size)
    for name, mask in masks.items():
        if name in names:
            union = ImageChops.lighter(union, mask)
        else:
            blocked = ImageChops.lighter(blocked, mask)
    bounds = union.getbbox()
    # The full group shares one artwork transform; never restart the pattern at
    # each island. A two-pixel RGB bleed fills guide edges but not other islands.
    allowed = ImageChops.multiply(union.filter(ImageFilter.MaxFilter(5)), ImageChops.invert(blocked))
    x0, y0, x1, y1 = bounds
    print_image = ImageOps.fit(artwork, (x1 - x0 + 4, y1 - y0 + 4), Image.Resampling.LANCZOS)
    patch = Image.new('RGBA', canvas.size)
    patch.paste(print_image, (x0 - 2, y0 - 2))
    patch.putalpha(ImageChops.multiply(patch.getchannel('A'), allowed))
    canvas.alpha_composite(patch)
    return {'parts': names, 'rotation_cw': rotation, 'mirror': mirror,
            'source_box': source_box, 'group_box': list(bounds), 'edge_bleed_px': 2,
            'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest()}


def place_layer(canvas, motif, mask, part, layer):
    inset = part['inset']
    safe = mask.filter(ImageFilter.MinFilter(2 * inset + 1))
    bounds = safe.getbbox()
    if not bounds:
        raise ValueError('part has no safe interior')
    x0, y0, x1, y1 = bounds
    # These are conservative design margins, not calibrated handle coordinates.
    if part.get('window_edge') == 'right':
        x1 -= round((x1 - x0) * .20)
    elif part.get('window_edge') == 'left':
        x0 += round((x1 - x0) * .20)
    if 'placement_box' in part:
        u0, v0, u1, v1 = part['placement_box']
        bw, bh = x1 - x0, y1 - y0
        x0, y0, x1, y1 = round(x0 + u0 * bw), round(y0 + v0 * bh), round(x0 + u1 * bw), round(y0 + v1 * bh)
    scale = number(layer.get('scale', .75), .05, 1, 'scale')
    center = layer.get('center', [.5, .5])
    if not isinstance(center, list) or len(center) != 2:
        raise ValueError('center must be [u, v]')
    u, v = (number(c, 0, 1, 'center') for c in center)
    rotation = layer.get('rotation_cw', part['rotation_cw'])
    if rotation not in (0, 90, 180, 270):
        raise ValueError('rotation_cw must be 0/90/180/270')
    if not isinstance(layer.get('mirror', False), bool):
        raise ValueError('mirror must be a boolean')
    if layer.get('mirror', False):
        motif = ImageOps.mirror(motif)
    motif = motif.rotate(-rotation, expand=True)
    max_w, max_h = (x1 - x0) * scale, (y1 - y0) * scale
    fit = min(max_w / motif.width, max_h / motif.height)
    cx, cy = x0 + u * (x1 - x0), y0 + v * (y1 - y0)
    # Fit visible art inside the actual irregular mask, not just its rectangle.
    for attempt in range(24):
        size = max(1, round(motif.width * fit)), max(1, round(motif.height * fit))
        art = motif.resize(size, Image.Resampling.LANCZOS)
        patch = Image.new('RGBA', canvas.size)
        patch.paste(art, (round(cx - art.width / 2), round(cy - art.height / 2)))
        opacity = patch.getchannel('A')
        # Do not silently accept subjects clipped by the outer canvas.
        total = sum(i * n for i, n in enumerate(art.getchannel('A').histogram()))
        inside = ImageChops.multiply(opacity, safe)
        remaining = sum(i * n for i, n in enumerate(inside.histogram()))
        if total and remaining == total:
            canvas.alpha_composite(patch)
            return {'rotation_cw': rotation, 'size': list(size), 'center_px': [round(cx), round(cy)],
                    'safe_inset': inset, 'fit_attempts': attempt + 1, 'clipped_pixels': 0}
        fit *= .9
    raise ValueError('motif cannot fit safe area; move center or choose a smaller motif')


def review_board(image, parts, masks, destination):
    """Flat orientation evidence only. Never present this as a vehicle preview."""
    board = Image.new('RGB', (1200, 740), '#edf1f3')
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    draw.text((24, 16), 'UV orientation proof - NOT a 3D / Tesla App preview. Actual App front/side/rear views still pending.', fill='#182b39', font=font)
    groups = [('HOOD / outside front', ['hood']), ('LEFT SIDE / common UV scale', ['left_front_fender', 'left_front_door', 'left_rear_door', 'left_rear_quarter']),
              ('RIGHT SIDE / common UV scale', ['right_front_fender', 'right_front_door', 'right_rear_door', 'right_rear_quarter']), ('REAR / mapping pending', ['rear_center'])]
    for index, (title, names) in enumerate(groups):
        ox, oy = (index % 2) * 600, 52 + (index // 2) * 344
        draw.rounded_rectangle((ox + 12, oy, ox + 588, oy + 330), 12, fill='white')
        draw.text((ox + 24, oy + 14), title, fill='#182b39', font=font)
        union = Image.new('L', image.size)
        for name in names:
            union = ImageChops.lighter(union, masks[name])
        crop = image.copy()
        crop.putalpha(union)
        crop = crop.crop(union.getbbox()).rotate(parts[names[0]]['rotation_cw'], expand=True)
        # Preserve the common UV scale and relative positions of the group.
        # Resizing each island separately hides discontinuities in shared prints.
        crop.thumbnail((544, 260), Image.Resampling.LANCZOS)
        px, py = ox + 28 + (544 - crop.width) // 2, oy + 46 + (260 - crop.height) // 2
        board.paste(crop, (px, py), crop)
    with Path(destination).open('xb') as output:
        board.save(output, format='PNG', optimize=True)


def compose(design_path, output_path, report_path=None, review_path=None):
    design_path, output_path = Path(design_path).resolve(), Path(output_path)
    paths = [output_path] + [Path(p) for p in (report_path, review_path) if p]
    if len({p.resolve() for p in paths}) != len(paths) or design_path in {p.resolve() for p in paths}:
        raise ValueError('output/report/review paths must be distinct and cannot replace the design')
    for p in paths:
        if p.exists():
            raise FileExistsError(f'output already exists: {p}')
    if output_path.suffix.lower() != '.png':
        raise ValueError('output must be PNG')
    design = json.loads(design_path.read_text(encoding='utf-8'))
    if not isinstance(design, dict):
        raise ValueError('design must be an object')
    template, parts, masks = template_parts()
    supplied = design.get('parts', {})
    if not isinstance(supplied, dict) or set(supplied) - set(parts):
        raise ValueError('parts must be an object using known Model Y part IDs')
    canvas = Image.new('RGBA', template.size, design.get('base_color', '#fff2df'))
    if canvas.getchannel('A').getextrema() != (255, 255):
        raise ValueError('base_color must be opaque')
    backgrounds = design.get('backgrounds', [])
    if not isinstance(backgrounds, list):
        raise ValueError('backgrounds must be a list')
    background_records = []
    for background in backgrounds:
        if not isinstance(background, dict):
            raise ValueError('each background must be an object')
        source = (design_path.parent / background['image']).resolve()
        if source in {p.resolve() for p in paths}:
            raise ValueError('output paths cannot replace background artwork')
        record = place_background(canvas, source, masks, background)
        record['image'] = background['image']
        background_records.append(record)
    cache, applied = {}, {}
    for name, layers in supplied.items():
        if not isinstance(layers, list):
            raise ValueError(f'{name}: layers must be a list')
        applied[name] = []
        for layer in layers:
            if not isinstance(layer, dict):
                raise ValueError(f'{name}: each layer must be an object')
            source = (design_path.parent / layer['image']).resolve()
            if source in {p.resolve() for p in paths}:
                raise ValueError('output paths cannot replace source artwork')
            if source not in cache:
                cache[source] = clean_motif(source)
            placement = place_layer(canvas, cache[source], masks[name], parts[name], layer)
            placement['image'] = layer['image']
            placement['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            applied[name].append(placement)
    # Template RGB includes guide outlines: use alpha only, never paint the guides.
    canvas.putalpha(template.getchannel('A'))
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('xb') as output:
        canvas.save(output, format='PNG', optimize=True)
    result = {'ok': True, 'canvas': [1024, 1024], 'template_alpha_exact': True,
              'viewing_convention': 'outside-front/side-upright', 'backgrounds': background_records, 'parts': applied,
              'sha256': hashlib.sha256(output_path.read_bytes()).hexdigest(),
              'checks': {'composition': 'passed', 'file': 'run validate_skin.py', 'visual': 'manual_required',
                         'app_front': 'pending', 'app_side': 'pending', 'app_rear': 'pending', 'vehicle': 'pending'}}
    if report_path:
        with Path(report_path).open('x', encoding='utf-8') as report:
            report.write(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    if review_path:
        review_board(canvas, parts, masks, review_path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    try:
        result = compose(args.design, args.output, args.report, args.review)
    except (OSError, ValueError, KeyError, TypeError, Image.DecompressionBombError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
