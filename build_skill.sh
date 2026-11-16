#!/usr/bin/env bash
# Package the agent skill as dist/trading-backtester.zip for upload to a skills marketplace.
set -euo pipefail

cd "$(dirname "$0")"
NAME=trading-backtester
BUILD=dist/$NAME

rm -rf dist
mkdir -p "$BUILD/scripts"

cp skill/$NAME/SKILL.md "$BUILD/"
cp backtester.py strategies.py metrics.py "$BUILD/scripts/"
grep -v '^pytest$' requirements.txt > "$BUILD/scripts/requirements.txt"
chmod +x "$BUILD/scripts/backtester.py"

(cd dist && zip -qr "$NAME.zip" "$NAME" -x '*/__pycache__/*' '*.DS_Store')
echo "Built dist/$NAME.zip"
