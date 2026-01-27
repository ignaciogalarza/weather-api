#!/bin/bash
# Install Git hooks for the Weather API project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing Git hooks..."

# Install pre-commit hook
cp "$SCRIPT_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✓ Pre-commit hook installed"
echo ""
echo "The pre-commit hook will run:"
echo "  - Ruff linting"
echo "  - MyPy type checking"
echo "  - All tests"
echo ""
echo "To skip hooks temporarily, use: git commit --no-verify"
