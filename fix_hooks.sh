#!/bin/bash
# Fix Eric Buess Tools Hook Issues
# Run this script to clean up and reinstall the tools properly

set -e  # Exit on error

echo "=================================="
echo "Eric Buess Tools Fix Script"
echo "=================================="
echo ""

# Step 1: Backup current settings
echo "📋 Step 1: Backing up Claude settings..."
if [ -f ~/.claude/settings.json ]; then
    cp ~/.claude/settings.json ~/.claude/settings.json.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✓ Backup created"
else
    echo "   ⚠️  No settings file found (this is okay)"
fi

# Step 2: Remove problematic hooks from settings
echo ""
echo "🔧 Step 2: Removing problematic hooks..."
if [ -f ~/.claude/settings.json ]; then
    python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"

if settings_path.exists():
    with open(settings_path, 'r') as f:
        settings = json.load(f)

    # Remove problematic hooks
    removed = []
    if 'hooks' in settings:
        if 'Stop' in settings['hooks']:
            del settings['hooks']['Stop']
            removed.append('Stop')

        if 'PostToolUse:Edit' in settings['hooks']:
            del settings['hooks']['PostToolUse:Edit']
            removed.append('PostToolUse:Edit')

        if 'PostToolUse:Write' in settings['hooks']:
            del settings['hooks']['PostToolUse:Write']
            removed.append('PostToolUse:Write')

    # Save updated settings
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    if removed:
        print(f"   ✓ Removed hooks: {', '.join(removed)}")
    else:
        print("   ✓ No problematic hooks found")
else:
    print("   ⚠️  Settings file not found")
PYTHON_SCRIPT
else
    echo "   ⚠️  No settings file to clean"
fi

# Step 3: Remove old installations
echo ""
echo "🗑️  Step 3: Removing old tool installations..."
if [ -d ~/.claude-code-project-index ]; then
    rm -rf ~/.claude-code-project-index
    echo "   ✓ Removed PROJECT_INDEX"
else
    echo "   ⚠️  PROJECT_INDEX not found (already removed)"
fi

if [ -d ~/.claude-code-docs ]; then
    rm -rf ~/.claude-code-docs
    echo "   ✓ Removed Claude Code Docs"
else
    echo "   ⚠️  Claude Code Docs not found (already removed)"
fi

# Step 4: Reinstall PROJECT_INDEX
echo ""
echo "📦 Step 4: Reinstalling PROJECT_INDEX tool..."
if curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-project-index/main/install.sh | bash; then
    echo "   ✓ PROJECT_INDEX installed"
else
    echo "   ❌ PROJECT_INDEX installation failed"
fi

# Step 5: Reinstall Claude Code Docs
echo ""
echo "📚 Step 5: Reinstalling Claude Code Docs tool..."
if curl -fsSL https://raw.githubusercontent.com/ericbuess/claude-code-docs/main/install.sh | bash; then
    echo "   ✓ Claude Code Docs installed"
else
    echo "   ❌ Claude Code Docs installation failed"
fi

# Step 6: Final cleanup - remove the new hooks that might cause issues
echo ""
echo "🔧 Step 6: Final hook cleanup..."
if [ -f ~/.claude/settings.json ]; then
    python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"

if settings_path.exists():
    with open(settings_path, 'r') as f:
        settings = json.load(f)

    # Remove the problematic hooks again (in case install added them back)
    removed = []
    if 'hooks' in settings:
        if 'Stop' in settings['hooks']:
            del settings['hooks']['Stop']
            removed.append('Stop')

        if 'PostToolUse:Edit' in settings['hooks']:
            del settings['hooks']['PostToolUse:Edit']
            removed.append('PostToolUse:Edit')

        if 'PostToolUse:Write' in settings['hooks']:
            del settings['hooks']['PostToolUse:Write']
            removed.append('PostToolUse:Write')

    # Save updated settings
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    if removed:
        print(f"   ✓ Removed hooks: {', '.join(removed)}")
    else:
        print("   ✓ No hooks to remove")
PYTHON_SCRIPT
fi

echo ""
echo "=================================="
echo "✅ Fix Complete!"
echo "=================================="
echo ""
echo "📋 Summary:"
echo "   - Old installations removed"
echo "   - Problematic hooks disabled"
echo "   - Tools reinstalled"
echo ""
echo "🎯 Next steps:"
echo "   1. Restart Claude Code"
echo "   2. Test with: /index"
echo "   3. Test with: help -i"
echo "   4. Test with: /docs hooks"
echo ""
echo "💡 Note: The -i flag should work, but automatic"
echo "   index updates on file save are disabled to"
echo "   prevent errors. Use /index manually when needed."
echo ""
