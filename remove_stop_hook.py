#!/usr/bin/env python3
"""
Remove the Stop hook from Claude Code settings to prevent errors.
Run this script: python3 remove_stop_hook.py
"""

import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"

print("Removing Stop hook from Claude Code settings...")
print(f"Settings file: {settings_path}")
print()

if not settings_path.exists():
    print("❌ Settings file not found!")
    exit(1)

# Backup first
backup_path = settings_path.parent / f"settings.json.backup.{int(__import__('time').time())}"
with open(settings_path, 'r') as f:
    content = f.read()
with open(backup_path, 'w') as f:
    f.write(content)
print(f"✅ Backup created: {backup_path}")

# Load settings
with open(settings_path, 'r') as f:
    settings = json.load(f)

# Remove Stop hook
removed = False
if 'hooks' in settings and 'Stop' in settings['hooks']:
    del settings['hooks']['Stop']
    removed = True
    print("✅ Removed Stop hook")
else:
    print("⚠️  Stop hook not found (already removed)")

# Save
if removed:
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print("✅ Settings saved")

print()
print("=" * 50)
print("NEXT STEP: Restart Claude Code")
print("=" * 50)
