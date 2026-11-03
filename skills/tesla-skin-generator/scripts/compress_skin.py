#!/usr/bin/env python3
"""Fit a static PNG into 1,000,000 bytes without resizing or changing alpha.

Try lossless re-encoding first, then 256/128/64/32 RGB colors. Never overwrite
the source or an existing destination. Compression success is not skin validation.
Requires Python 3 and Pillow.
"""

import argparse
import io
import json
import sys
from pathlib import Path

try:
    from PIL import Image, PngImagePlugin
except ImportError:
    print('Missing Pillow: python -m pip install Pillow', file=sys.stderr)
    raise SystemExit(2)

MAX_BYTES = 1_000_000


def encode_png(image, metadata):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True, compress_level=9, **metadata)
    return buffer.getvalue()


def compress_png(source, destination, max_bytes=MAX_BYTES):
    source, destination = Path(source), Path(destination)
    if not 0 < max_bytes <= MAX_BYTES:
        raise ValueError('limit must be positive and no larger than 1,000,000 bytes')
    if destination.resolve() == source.resolve():
        raise ValueError('destination must differ from source')
    if destination.exists():
        raise FileExistsError(f'destination already exists: {destination}')
    if destination.suffix.lower() != '.png':
        raise ValueError('destination must have a .png extension')

    original_bytes = source.read_bytes()
    with Image.open(io.BytesIO(original_bytes)) as original:
        if original.format != 'PNG' or getattr(original, 'n_frames', 1) != 1:
            raise ValueError('source must be a single-frame PNG')
        original.load()
        image = original.convert('RGBA')
        # Retain color interpretation, discard nonessential text/EXIF metadata.
        metadata = {}
        if original.info.get('icc_profile'):
            metadata['icc_profile'] = original.info['icc_profile']
        color_info = PngImagePlugin.PngInfo()
        if 'srgb' in original.info:
            color_info.add(b'sRGB', bytes([original.info['srgb']]))
        if 'gamma' in original.info:
            value = round(original.info['gamma'] * 100000)
            color_info.add(b'gAMA', value.to_bytes(4, 'big'))
        if 'chromaticity' in original.info:
            values = original.info['chromaticity']
            color_info.add(b'cHRM', b''.join(round(v * 100000).to_bytes(4, 'big') for v in values))
        metadata['pnginfo'] = color_info
        image.info.clear()

    alpha = image.getchannel('A')
    attempts = []
    method, lossy, selected = 'unchanged', False, original_bytes
    if len(selected) > max_bytes:
        selected = encode_png(image, metadata)
        method = 'lossless'
        attempts.append({'method': method, 'bytes': len(selected)})
        if len(selected) > max_bytes:
            rgb = image.convert('RGB')
            # Invisible RGB should not consume palette entries. Alpha stays exact.
            rgb.paste((0, 0, 0), mask=alpha.point(lambda p: 255 if p == 0 else 0))
            for colors in (256, 128, 64, 32):
                candidate = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                                         dither=Image.Dither.NONE).convert('RGBA')
                candidate.putalpha(alpha)
                selected = encode_png(candidate, metadata)
                method, lossy = f'quantized-{colors}', True
                attempts.append({'method': method, 'bytes': len(selected)})
                if len(selected) <= max_bytes:
                    break
        if len(selected) > max_bytes:
            raise ValueError(f'cannot fit within {max_bytes} bytes while retaining dimensions/alpha; '
                             f'last attempt {len(selected)} bytes; original retained, no output written')

    # Check the encoded output itself, not only the in-memory working image.
    with Image.open(io.BytesIO(selected)) as check:
        decoded = check.convert('RGBA')
        if decoded.size != image.size or decoded.getchannel('A').tobytes() != alpha.tobytes():
            raise ValueError('encoded PNG changed dimensions or alpha; no output written')
        if not lossy and decoded.tobytes() != image.tobytes():
            raise ValueError('lossless encoding changed pixel data; no output written')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as target:
        target.write(selected)
    return {
        'ok': True, 'source': str(source), 'output': str(destination),
        'input_bytes': len(original_bytes), 'output_bytes': len(selected),
        'max_bytes': max_bytes, 'method': method, 'lossy_rgb': lossy,
        'size': list(image.size), 'alpha_preserved': True, 'attempts': attempts,
        'warning': 'File-size success does not verify Model Y geometry, direction or in-car appearance.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, help='Optional new JSON compression report')
    args = parser.parse_args()
    if args.report:
        if args.report.resolve() in (args.source.resolve(), args.output.resolve()):
            parser.error('report must not replace source or output')
        if args.report.exists():
            parser.error('report already exists')
    try:
        result = compress_png(args.source, args.output)
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=True, indent=2))
        return 1
    payload = json.dumps(result, ensure_ascii=True, indent=2)
    print(payload)
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open('x', encoding='utf-8') as target:
                target.write(payload + '\n')
        except OSError as exc:
            print(f'PNG saved, but compression report could not be saved: {exc}', file=sys.stderr)
            return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
