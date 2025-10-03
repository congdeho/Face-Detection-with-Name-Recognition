#!/bin/bash
# Git configuration script for Windows line endings

echo "🔧 Configuring Git line endings for cross-platform compatibility..."

# Set autocrlf to true for Windows (converts LF to CRLF on checkout, CRLF to LF on commit)
git config --global core.autocrlf true

echo "✅ Set core.autocrlf = true"

# Optional: Set safecrlf to warn about mixed line endings
git config --global core.safecrlf warn

echo "✅ Set core.safecrlf = warn"

echo ""
echo "📋 Current Git configuration:"
git config --list | grep "core\."

echo ""
echo "✨ Git line endings configuration completed!"
echo ""
echo "📝 What this means:"
echo "   - Files will be stored with LF endings in the repository"
echo "   - Files will be checked out with CRLF endings on Windows"
echo "   - This ensures cross-platform compatibility"
echo ""
echo "🚀 You can now safely commit your files!"