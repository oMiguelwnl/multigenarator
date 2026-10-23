"""Check new commit messages without executing code from the reviewed branch."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HOOK = Path(__file__).resolve().parents[1] / '.githooks/commit-msg'


def sha(value):
    if not re.fullmatch(r'[0-9a-f]{40}', value):
        raise argparse.ArgumentTypeError('expected a full commit SHA')
    return value


def validate(message):
    with tempfile.TemporaryDirectory(prefix='commit-policy-') as tmp:
        path = Path(tmp) / 'message'
        path.write_bytes(message)
        return subprocess.run([sys.executable, str(HOOK), str(path)], check=False).returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=sha, required=True)
    parser.add_argument('--head', type=sha, required=True)
    parser.add_argument('--grandfather', type=sha, action='append', default=[])
    parser.add_argument('--title', default='')
    args = parser.parse_args()
    if args.title and not validate(args.title.encode('utf-8')):
        return 1
    try:
        commits = subprocess.check_output([
            'git', 'rev-list', args.head, '^' + args.base,
            *['^' + ref for ref in args.grandfather], '--',
        ], text=True).splitlines()
        failures = []
        for commit in commits:
            message = subprocess.check_output(['git', 'show', '-s', '--format=%B', commit])
            if not validate(message):
                failures.append(commit)
        if failures:
            print('Conventional Commits: invalid commits: ' + ', '.join(failures), file=sys.stderr)
            return 1
        print(f'Conventional Commits: {len(commits)} new commits validated.')
        return 0
    except subprocess.CalledProcessError:
        print('Conventional Commits: incomplete Git history; validation failed.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
