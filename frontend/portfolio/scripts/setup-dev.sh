#!/bin/bash

# Setup script for development environment
# This installs git hooks and sets up the local testing environment

echo "🛠️  Setting up portfolio development environment..."

# Install git hooks
echo "📦 Installing git hooks..."
cp scripts/git-hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Install required tools if not present
echo "🔧 Checking required tools..."

# Check if flake8 is installed
if ! command -v flake8 &> /dev/null; then
    echo "📦 Installing flake8..."
    pip install flake8
fi

# Check if bandit is installed
if ! command -v bandit &> /dev/null; then
    echo "📦 Installing bandit..."
    pip install bandit
fi

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  ./scripts/pre-push-check.sh  - Run full validation pipeline"
echo "  git push                     - Automatically runs validation before push"
echo ""
echo "🔒 The pre-push hook will now prevent pushes with errors!"