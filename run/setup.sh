#!/usr/bin/env bash
set -euo pipefail

# Basic setup for Codex environment
echo "Initializing Codex setup..."

# Install pre-commit hooks if available
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install >/dev/null
fi

# Build static assets when package.json is present
if [ -f package.json ]; then
    npm run build || true
fi
