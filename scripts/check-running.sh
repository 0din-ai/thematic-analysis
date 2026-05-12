#!/usr/bin/env bash
# Check for running instances of the Thematic Analysis app.
#
# Usage:
#   bash scripts/check-running.sh          # check only
#   bash scripts/check-running.sh --kill   # kill all instances

set -euo pipefail

pids=$(lsof -ti :5111 2>/dev/null || true)

if [ -z "$pids" ]; then
    echo "No instances running on port 5111."
    exit 0
fi

echo "Found instance(s) on port 5111:"
lsof -i :5111 -P

if [ "${1:-}" = "--kill" ]; then
    echo ""
    for pid in $pids; do
        echo "Killing PID $pid..."
        kill "$pid"
    done
    echo "Done."
else
    echo ""
    echo "Run with --kill to stop them."
fi
