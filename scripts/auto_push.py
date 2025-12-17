#!/usr/bin/env python3
"""
Simple watcher that auto-commits and pushes repository changes.

Usage:
  python3 scripts/auto_push.py --path .

Requirements:
  pip install watchdog

Notes:
  - The script expects a valid git repo with a configured remote (e.g. 'origin').
  - It will only commit when there are staged/uncommitted changes.
  - For macOS automatic startup, use the provided LaunchAgent plist example.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from threading import Timer, Lock

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, repo_path: Path, delay: float = 1.0):
        super().__init__()
        self.repo = repo_path.resolve()
        self.delay = delay
        self._timer = None
        self._lock = Lock()

    def _schedule(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = Timer(self.delay, self._commit_and_push)
            self._timer.start()

    def on_any_event(self, event):
        if event.is_directory:
            return
        # ignore .git changes
        if '/.git/' in event.src_path.replace('\\', '/'):
            return
        self._schedule()

    def _run(self, *args):
        return subprocess.run(args, cwd=self.repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _has_changes(self):
        r = self._run('git', 'status', '--porcelain')
        return bool(r.stdout.strip())

    def _commit_and_push(self):
        with self._lock:
            # stage all
            self._run('git', 'add', '-A')
            if not self._has_changes():
                return
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            msg = f'Auto update: {timestamp}'
            self._run('git', 'commit', '-m', msg)
            # attempt push; rely on user's git auth (ssh key or credential helper)
            self._run('git', 'push')


def main():
    parser = argparse.ArgumentParser(description='Auto-commit and push on file changes')
    parser.add_argument('--path', '-p', default='.', help='Path to repository (default: .)')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Debounce delay seconds')
    args = parser.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / '.git').exists():
        print('Error: path is not a git repository (no .git found).', file=sys.stderr)
        sys.exit(1)

    event_handler = DebouncedHandler(repo, delay=args.delay)
    observer = Observer()
    observer.schedule(event_handler, str(repo), recursive=True)
    observer.start()
    try:
        print('Watching', repo)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
