#!/usr/bin/env bash
# Build the Thematic Analysis macOS .app bundle.
#
# Usage:
#   bash scripts/build-macos.sh
#
# Prerequisites:
#   - uv (Python package manager)
#   - macOS with arm64 architecture

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1/4  Installing dependencies ==="
uv sync --extra build

echo ""
echo "=== 2/4  Downloading tiktoken data ==="
uv run python scripts/download_tiktoken_data.py

echo ""
echo "=== 3/4  Running PyInstaller ==="
uv run pyinstaller thematic-analysis.spec --noconfirm --clean

echo ""
echo "=== 4/4  Verifying bundle ==="
APP="dist/Thematic Analysis.app"
CONTENTS="$APP/Contents"

errors=0

if [ ! -d "$APP" ]; then
    echo "ERROR: $APP not found"
    exit 1
fi

# Check critical bundled files
for f in \
    "Resources/thematic_analysis/templates/index.html" \
    "Resources/prompts/default-prompts.md" \
; do
    if [ -f "$CONTENTS/$f" ]; then
        echo "  OK: $f"
    else
        echo "  MISSING: $f"
        errors=$((errors + 1))
    fi
done

# Check tiktoken cache has files
CACHE_DIR="$CONTENTS/Resources/tiktoken_cache"
if [ -d "$CACHE_DIR" ]; then
    count=$(ls -1 "$CACHE_DIR" | wc -l | tr -d ' ')
    if [ "$count" -ge 2 ]; then
        echo "  OK: tiktoken_cache ($count files)"
    else
        echo "  WARNING: tiktoken_cache has only $count files (expected >= 2)"
        errors=$((errors + 1))
    fi
else
    echo "  MISSING: tiktoken_cache directory"
    errors=$((errors + 1))
fi

echo ""
if [ "$errors" -gt 0 ]; then
    echo "Build completed with $errors error(s). Check output above."
    exit 1
else
    echo "Build successful: $APP"
    echo "Size: $(du -sh "$APP" | cut -f1)"
fi
