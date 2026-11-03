#!/usr/bin/env python3
"""Validate and reproducibly package the standalone skill. Requires dev deps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
NAME = 'tesla-skin-generator'
VERSION_RE = re.compile(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)')
TEXT_SUFFIXES = {'.md', '.py', '.json', '.yaml', '.yml', '.txt'}


def parse_version(value):
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        raise ValueError(f'invalid stable SemVer: {value!r}')
    return tuple(map(int, value.split('.')))


def skill_path(root):
    return Path(root) / 'skills' / NAME


def frontmatter(path):
    text = Path(path).read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if not match:
        raise ValueError('SKILL.md must start with YAML frontmatter')
    metadata = yaml.safe_load(match[1])
    if not isinstance(metadata, dict):
        raise ValueError('SKILL.md frontmatter must be an object')
    return text, match, metadata


def read_version(root=ROOT):
    version = (skill_path(root) / 'VERSION').read_text(encoding='utf-8').strip()
    parse_version(version)
    return version


def set_version(root, version):
    parse_version(version)
    skill = skill_path(root)
    text, match, data = frontmatter(skill / 'SKILL.md')
    data.setdefault('metadata', {})['version'] = version
    header = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000).rstrip()
    (skill / 'SKILL.md').write_text('---\n' + header + '\n---\n' + text[match.end():], encoding='utf-8')
    (skill / 'VERSION').write_text(version + '\n', encoding='utf-8')


def validate_skill(root=ROOT):
    root, skill = Path(root), skill_path(root)
    version = read_version(root)
    _, _, data = frontmatter(skill / 'SKILL.md')
    if data.get('name') != NAME or not isinstance(data.get('description'), str) or not data['description'].strip():
        raise ValueError('invalid skill name or description')
    if data.get('metadata', {}).get('version') != version:
        raise ValueError('VERSION and SKILL.md metadata.version differ')
    ui = yaml.safe_load((skill / 'agents/openai.yaml').read_text(encoding='utf-8'))['interface']
    if not 25 <= len(ui['short_description']) <= 64 or '$' + NAME not in ui['default_prompt']:
        raise ValueError('invalid skill UI metadata')
    for doc in [skill / 'SKILL.md', *sorted((skill / 'references').glob('*.md'))]:
        text = doc.read_text(encoding='utf-8')
        if re.search(r'^\s*\[TODO:', text, re.MULTILINE):
            raise ValueError(f'unfinished instructions: {doc.name}')
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if not link.startswith(('https://', 'http://', '#')) and not (doc.parent / link.split('#')[0]).is_file():
                raise ValueError(f'broken skill reference: {doc.name}: {link}')
    for script in (skill / 'scripts').glob('*.py'):
        compile(script.read_text(encoding='utf-8'), script.name, 'exec')
    config = json.loads((skill / 'assets/parts.json').read_text(encoding='utf-8'))
    template = skill / 'assets/template.png'
    if hashlib.sha256(template.read_bytes()).hexdigest() != config['template_sha256']:
        raise ValueError('template hash differs from calibrated UV template')
    with Image.open(template) as image:
        if image.format != 'PNG' or image.size != (1024, 1024) or image.mode != 'RGBA':
            raise ValueError('invalid template PNG')
    if len(config['parts']) != 16 or not (root / 'LICENSE').is_file():
        raise ValueError('missing part definitions or license')
    return version


def normalized_bytes(path):
    content = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in ('VERSION', 'LICENSE'):
        content = content.decode('utf-8').replace('\r\n', '\n').encode('utf-8')
    return content


def build(root=ROOT, output=None, source_sha=None):
    root = Path(root)
    version = validate_skill(root)
    output = Path(output) if output is not None else root / 'dist'
    if source_sha is None:
        source_sha = os.environ.get('GITHUB_SHA') or subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40,64}', source_sha):
        raise ValueError('source commit must be a full Git commit hash')
    skill = skill_path(root)
    members = {}
    for path in sorted(skill.rglob('*')):
        rel = path.relative_to(skill)
        if not path.is_file() or any(p.startswith('.') or p == '__pycache__' for p in rel.parts) or path.suffix == '.pyc':
            continue
        if rel.parts[0] not in {'SKILL.md', 'VERSION', 'agents', 'assets', 'references', 'scripts'}:
            continue
        members[rel.as_posix()] = normalized_bytes(path)
    members['LICENSE'] = normalized_bytes(root / 'LICENSE')
    manifest = {'name': NAME, 'version': version, 'source_commit': source_sha,
                'files': {name: hashlib.sha256(content).hexdigest() for name, content in sorted(members.items())}}
    members['BUILD.json'] = (json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode('utf-8')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'{NAME}-v{version}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, content in sorted(members.items()):
            info = zipfile.ZipInfo(f'{NAME}/{name}', date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        for name, expected in manifest['files'].items():
            if hashlib.sha256(package.read(f'{NAME}/{name}')).hexdigest() != expected:
                raise ValueError(f'packaged file hash mismatch: {name}')
    return {'version': version, 'archive': str(archive), 'sha256': digest, 'source_commit': source_sha}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-sha')
    args = parser.parse_args()
    if args.check:
        print(json.dumps({'ok': True, 'version': validate_skill()}))
    else:
        print(json.dumps(build(output=args.output, source_sha=args.source_sha), indent=2))


if __name__ == '__main__':
    main()
