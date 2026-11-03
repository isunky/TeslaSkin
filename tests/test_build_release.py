"""Version/package checks plus real local Git release/retry integration."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_skill as builder
import release_skill as releaser


class BuildReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'work'
        self.root.mkdir()
        shutil.copytree(ROOT / 'skills' / builder.NAME, self.root / 'skills' / builder.NAME,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'LICENSE', self.root / 'LICENSE')

    def setup_git(self):
        self.remote = self.base / 'remote.git'
        releaser.git(self.base, 'init', '--bare', str(self.remote))
        releaser.git(self.root, 'init', '-b', 'main')
        releaser.git(self.root, 'config', 'user.name', 'Release Test')
        releaser.git(self.root, 'config', 'user.email', 'release-test@example.invalid')
        releaser.git(self.root, 'config', 'commit.gpgsign', 'false')
        releaser.git(self.root, 'remote', 'add', 'origin', str(self.remote))
        releaser.git(self.root, 'add', '.')
        releaser.git(self.root, 'commit', '-m', 'Initial test source')
        releaser.git(self.root, 'push', '-u', 'origin', 'main')
        return releaser.git(self.root, 'rev-parse', 'HEAD')

    def test_version_parser_and_bumps(self):
        self.assertEqual(releaser.next_version('0.1.0', []), '0.1.0')
        self.assertEqual(releaser.next_version('0.1.0', ['v0.1.0']), '0.1.1')
        self.assertEqual(releaser.next_version('0.1.0', ['v0.9.0', 'v0.10.0', 'not-a-release']), '0.10.1')
        self.assertEqual(releaser.next_version('0.1.9', ['v0.1.9'], 'minor'), '0.2.0')
        self.assertEqual(releaser.next_version('0.1.9', ['v0.1.9'], 'major'), '1.0.0')
        with self.assertRaises(ValueError): builder.parse_version('01.2.3')
        with self.assertRaises(ValueError): builder.parse_version('1.2')

    def test_version_update_keeps_skill_consistent(self):
        before, match, _ = builder.frontmatter(builder.skill_path(self.root) / 'SKILL.md')
        body = before[match.end():]
        builder.set_version(self.root, '2.3.4')
        self.assertEqual(builder.validate_skill(self.root), '2.3.4')
        after, match, _ = builder.frontmatter(builder.skill_path(self.root) / 'SKILL.md')
        self.assertEqual(after[match.end():], body)

    def test_mismatched_version_fails_build(self):
        (builder.skill_path(self.root) / 'VERSION').write_text('9.9.9\n')
        with self.assertRaisesRegex(ValueError, 'differ'):
            builder.build(self.root, self.base / 'dist', 'a' * 40)

    def test_deterministic_package_has_version_license_and_file_hashes(self):
        skill = builder.skill_path(self.root)
        (skill / '__pycache__').mkdir()
        (skill / '__pycache__/ignored.pyc').write_bytes(b'cache')
        (skill / '.env').write_text('LOCAL_ONLY=1\n')
        first = builder.build(self.root, self.base / 'one', 'a' * 40)
        second = builder.build(self.root, self.base / 'two', 'a' * 40)
        self.assertEqual(Path(first['archive']).read_bytes(), Path(second['archive']).read_bytes())
        with zipfile.ZipFile(first['archive']) as archive:
            names = archive.namelist()
            self.assertFalse(any('__pycache__' in n or '.env' in n for n in names))
            self.assertIn(f'{builder.NAME}/LICENSE', names)
            manifest = json.loads(archive.read(f'{builder.NAME}/BUILD.json'))
            self.assertEqual(manifest['version'], builder.read_version(self.root))
            self.assertEqual(manifest['source_commit'], 'a' * 40)
            for name, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read(f'{builder.NAME}/{name}')).hexdigest(), digest)
        self.assertIn(first['sha256'], (self.base / 'one/SHA256SUMS.txt').read_text())

    def test_cross_platform_newlines_do_not_change_package(self):
        first = builder.build(self.root, self.base / 'one', 'b' * 40)
        for path in builder.skill_path(self.root).rglob('*'):
            if path.is_file() and path.suffix in builder.TEXT_SUFFIXES:
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        second = builder.build(self.root, self.base / 'two', 'b' * 40)
        self.assertEqual(first['sha256'], second['sha256'])

    def test_broken_reference_is_rejected(self):
        path = builder.skill_path(self.root) / 'references/design.md'
        path.write_text(path.read_text(encoding='utf-8') + '\n[missing](missing.md)\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'broken skill reference'):
            builder.validate_skill(self.root)

    def test_first_release_retry_then_automatic_patch(self):
        source = self.setup_git()
        initial = builder.read_version(self.root)
        first = releaser.prepare_release(self.root, source)
        self.assertEqual(first['version'], initial)
        self.assertFalse(first['resumed'])
        self.assertNotEqual(first['release_commit'], source)
        retry = releaser.prepare_release(self.root, source)
        self.assertTrue(retry['resumed'])
        self.assertEqual(retry['version'], first['version'])
        self.assertEqual(retry['sha256'], first['sha256'])
        releaser.git(self.root, 'checkout', '-B', 'main', first['release_commit'])
        (self.root / 'change.txt').write_text('new code\n')
        releaser.git(self.root, 'add', 'change.txt')
        releaser.git(self.root, 'commit', '-m', 'Next source change')
        next_source = releaser.git(self.root, 'rev-parse', 'HEAD')
        releaser.git(self.root, 'push', 'origin', 'main')
        second = releaser.prepare_release(self.root, next_source)
        self.assertEqual(second['version'], releaser.next_version(initial, [f'v{initial}']))
        self.assertNotEqual(first['tag'], second['tag'])

    def test_stale_tested_commit_cannot_publish_over_new_main(self):
        source = self.setup_git()
        (self.root / 'newer.txt').write_text('new source\n')
        releaser.git(self.root, 'add', 'newer.txt')
        releaser.git(self.root, 'commit', '-m', 'New source ahead of tested commit')
        current = releaser.git(self.root, 'rev-parse', 'HEAD')
        releaser.git(self.root, 'push', 'origin', 'main')
        result = releaser.prepare_release(self.root, source)
        self.assertTrue(result['skip'])
        self.assertEqual(releaser.git(self.root, 'rev-parse', 'origin/main'), current)
        self.assertEqual(releaser.git(self.root, 'tag', '--list'), '')


if __name__ == '__main__':
    unittest.main()
