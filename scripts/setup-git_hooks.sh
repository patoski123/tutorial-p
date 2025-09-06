#!/bin/bash
echo "Installing git hooks..."
mkdir -p .git/hooks
cp git_hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo "✅ Hooks installed. Duplicate checks will run on git push."