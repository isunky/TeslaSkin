#!/usr/bin/env python3
"""Prepare a serialized, retryable release from a tested main commit.

Only the Actions release job calls this script. Uses normal atomic Git push,
never force-push; source code is not modified except version metadata and ZIP.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from build_skill import NAME, ROOT, build, parse_version, read_version, set_version


def git(root, *args):
    run = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, encoding='utf-8')
    if run.returncode:
        raise RuntimeError(run.stderr.strip() or run.stdout.strip())
    return run.stdout.strip()


def next_version(current, tags, bump='patch'):
    current_parts = parse_version(current)
    versions = []
    for tag in tags:
        try:
            if tag.startswith('v'):
                versions.append(parse_version(tag[1:]))
        except ValueError:
            continue
    if bump not in ('patch', 'minor', 'major'):
        raise ValueError('unknown version bump')
    if not versions and bump == 'patch':
        return current  # Bootstrap the first release at the declared base version.
    major, minor, patch = max([current_parts, *versions])
    if bump == 'major': major, minor, patch = major + 1, 0, 0
    elif bump == 'minor': minor, patch = minor + 1, 0
    else: patch += 1
    return f'{major}.{minor}.{patch}'


def prepare_release(root, source_sha, bump='patch'):
    root = Path(root)
    source_sha = git(root, 'rev-parse', f'{source_sha}^{{commit}}')
    git(root, 'fetch', 'origin', 'main', '--tags')
    remote_head = git(root, 'rev-parse', 'origin/main')
    resumed = False
    if remote_head != source_sha:
        message = git(root, 'show', '-s', '--format=%B', remote_head)
        parents = git(root, 'show', '-s', '--format=%P', remote_head).split()
        if parents != [source_sha] or f'Source-Commit: {source_sha}' not in message.splitlines() or not message.startswith('chore(release): v'):
            return {'skip': True, 'reason': 'main advanced; a newer run owns publication'}
        version = git(root, 'show', f'{remote_head}:skills/{NAME}/VERSION').strip()
        # Rerunning this workflow resumes its existing release instead of
        # incrementing again. A genuinely newer source commit is left alone.
        if (f'Release-Version: {version}' not in message.splitlines()
                or not message.startswith(f'chore(release): v{version} [skip ci]')):
            return {'skip': True, 'reason': 'main advanced; a newer run owns publication'}
        parse_version(version)
        git(root, 'checkout', '--detach', remote_head)
        resumed = True
    else:
        git(root, 'checkout', '--detach', source_sha)
        version = next_version(read_version(root), git(root, 'tag', '--list', 'v*').splitlines(), bump)
        set_version(root, version)
    result = build(root, root / 'dist', source_sha)
    alias = root / f'{NAME}.zip'
    if resumed:
        if alias.read_bytes() != Path(result['archive']).read_bytes():
            raise ValueError('retry build differs from the recorded release archive')
    else:
        shutil.copy2(result['archive'], alias)
        git(root, 'add', f'skills/{NAME}/VERSION', f'skills/{NAME}/SKILL.md', alias.name)
        git(root, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-m', f'chore(release): v{version} [skip ci]', '-m',
            f'Source-Commit: {source_sha}\nRelease-Version: {version}')
        remote_head = git(root, 'rev-parse', 'HEAD')
    tag = f'v{version}'
    existing = git(root, 'tag', '--list', tag)
    if existing:
        if git(root, 'rev-parse', f'{tag}^{{commit}}') != remote_head:
            raise ValueError('release tag already points at a different commit')
    else:
        git(root, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'tag', '-a', tag, '-m', f'{NAME} {version}; source {source_sha}', remote_head)
    if not resumed:
        try:
            git(root, 'push', '--atomic', 'origin', f'{remote_head}:refs/heads/main', f'refs/tags/{tag}')
        except RuntimeError:
            git(root, 'fetch', 'origin', 'main')
            if git(root, 'rev-parse', 'origin/main') != source_sha:
                return {'skip': True, 'reason': 'main advanced during publish; no force push attempted'}
            raise
    else:
        # Atomic publication means the tag and release commit must both exist.
        remote_tag = git(root, 'ls-remote', 'origin', f'refs/tags/{tag}^{{}}')
        if not remote_tag.startswith(remote_head + '\t'):
            raise ValueError('remote release tag is missing or differs')
    notes = (f'## {NAME} v{version}\n\n'
             f'- Source commit tested on Windows and Linux: `{source_sha}`\n'
             f'- Release commit: `{remote_head}`\n'
             '- Extract the ZIP into your personal skills directory.\n'
             '- VERSION, SKILL.md metadata and BUILD.json record the same version.\n'
             '- SHA256SUMS.txt verifies the archive; BUILD.json verifies packaged files.\n')
    (root / 'dist/release-notes.md').write_text(notes, encoding='utf-8')
    return {'skip': False, 'version': version, 'tag': tag, 'release_commit': remote_head,
            'source_commit': source_sha, 'resumed': resumed, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sha', default=os.environ.get('GITHUB_SHA'), required=not os.environ.get('GITHUB_SHA'))
    parser.add_argument('--bump', choices=('patch', 'minor', 'major'), default='patch')
    args = parser.parse_args()
    result = prepare_release(ROOT, args.source_sha, args.bump)
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as stream:
            for key in ('skip', 'version', 'tag', 'release_commit', 'source_commit'):
                if key in result:
                    value = str(result[key]).lower() if isinstance(result[key], bool) else str(result[key])
                    stream.write(f'{key}={value}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
