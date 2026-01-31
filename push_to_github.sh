#!/usr/bin/env bash
# Push Solar-Direct Simulator to https://github.com/shruthisenthilarasu/SolarEnergyManagement
set -e

cd "$(dirname "$0")"
REPO_URL="https://github.com/shruthisenthilarasu/SolarEnergyManagement.git"

echo "→ Initializing git..."
git init
git add -A
git status

echo ""
echo "→ Committing..."
git commit -m "Initial commit: Solar-Direct Energy Management Simulator"

echo ""
echo "→ Setting branch to main..."
git branch -M main

echo ""
echo "→ Adding remote origin..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo ""
echo "→ Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! View at: https://github.com/shruthisenthilarasu/SolarEnergyManagement"
