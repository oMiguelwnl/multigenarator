"""Git integration tests for the remote commit policy."""
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/check_commit_range.py'


class CommitRangeTests(unittest.TestCase):
    def test_history_exemption_and_new_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()
            git('init', '-b', 'main')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'commit.gpgsign', 'false')
            git('config', 'core.hooksPath', str(root / 'no-hooks'))
            git('commit', '--allow-empty', '-m', 'old legacy title')
            base = git('rev-parse', 'HEAD')
            git('commit', '--allow-empty', '-m', 'legacy feature title')
            legacy = git('rev-parse', 'HEAD')
            def check(head, title='feat: new work', exemption=legacy):
                return subprocess.run([sys.executable, str(SCRIPT), '--base', base,
                    '--head', head, '--grandfather', exemption, '--title', title], cwd=root,
                    capture_output=True, text=True)
            result = check(legacy)
            self.assertEqual(result.returncode, 0, result.stderr)
            git('commit', '--allow-empty', '-m', 'fix: correct data')
            valid = git('rev-parse', 'HEAD')
            self.assertEqual(check(valid).returncode, 0)
            self.assertNotEqual(check(valid, title='bad title').returncode, 0)
            git('commit', '--allow-empty', '-m', 'bad new title')
            result = check(git('rev-parse', 'HEAD'))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Conventional Commits', result.stderr)
            self.assertNotEqual(check('--all').returncode, 0)


if __name__ == '__main__':
    unittest.main()
