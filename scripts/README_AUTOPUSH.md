# Auto-push setup

Steps to enable automatic push on file changes (macOS):

1. Ensure this folder is a git repository and remote is configured:

```bash
cd /path/to/repo
git init            # if not already
git remote add origin <your-repo-url>  # if not already
```

2. Install Python dependency:

```bash
python3 -m pip install --user watchdog
```

3. Run the watcher manually (for testing):

```bash
python3 scripts/auto_push.py --path .
```

4. To run automatically on login (macOS), copy the provided plist to `~/Library/LaunchAgents/` and load it:

```bash
cp scripts/com.github.pajaksmart.autopush.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.github.pajaksmart.autopush.plist
```

Notes:
- The script relies on your git authentication (SSH key or credential helper). Ensure `git push` works from the command line without interactive prompts.
- Adjust the plist `ProgramArguments` to point to your Python executable if needed.
