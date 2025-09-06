# scripts/setup-hooks.sh (tracked in git)
#!/bin/bash
echo "Installing git hooks..."
cp git_hooks/pre-push .git/git_hooks/pre-push
chmod +x .git/git_hooks/pre-push
echo "✅ Hooks installed. Duplicate checks will run on git push."