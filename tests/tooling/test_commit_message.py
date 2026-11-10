"""Exercise actual Git commits with the project's English commit-msg hook enabled."""
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / ".githooks"


class CommitMessageTests(unittest.TestCase):
    def test_hook_exists(self) -> None:
        self.assertTrue((HOOKS / "commit-msg").is_file())

    def test_real_commits_and_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args: str, cwd: Path = root) -> subprocess.CompletedProcess[str]:
                return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

            self.assertEqual(git("init", "-b", "main").returncode, 0)
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            git("config", "commit.gpgsign", "false")
            git("config", "core.hooksPath", str(HOOKS))

            invalid_messages = [
                "update things",
                "feat: ",
                "unknown: change",
                "fix:no space",
                "Merge branch feature/x",
                "fix: valid\nbody without blank line",
                "feat: adiciona idioma",
                "fix(audio): corrige cache",
                "chore(merge): integra feature/x",
                "revert: desfaz mudança",
            ]
            for message in invalid_messages:
                with self.subTest(invalid=message):
                    result = git("commit", "--allow-empty", "-m", message)
                    self.assertNotEqual(result.returncode, 0)

            valid_messages = [
                "feat: add language support",
                "fix(audio): prevent stale cache reuse",
                "feat(api)!: remove legacy endpoint",
                "refactor: update contract\n\nBREAKING CHANGE: require new payload format",
                "chore(merge): merge feature/x",
                "revert: revert cache change",
            ]
            for message in valid_messages:
                with self.subTest(valid=message):
                    result = git("commit", "--allow-empty", "-m", message)
                    self.assertEqual(result.returncode, 0, result.stderr)

            other = root / "linked"
            self.assertEqual(git("worktree", "add", "-b", "feature/test", str(other)).returncode, 0)
            self.assertNotEqual(git("commit", "--allow-empty", "-m", "invalid", cwd=other).returncode, 0)
            result = git("commit", "--allow-empty", "-m", "test: verify worktree hook", cwd=other)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
