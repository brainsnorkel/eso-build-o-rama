#!/bin/bash
# Pre-merge check script - Run this before merging to main
#
# Usage:
#   ./scripts/pre-merge-check.sh [output-dir]
#
# Example:
#   ./scripts/pre-merge-check.sh output-dev

set -e  # Exit on error

OUTPUT_DIR="${1:-output-dev}"
CURRENT_BRANCH=$(git branch --show-current)

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              PRE-MERGE TO MAIN - SANITY CHECK                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Current branch: $CURRENT_BRANCH"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Step 1: Check if output directory exists
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "⚠️  Output directory '$OUTPUT_DIR' not found"
    echo ""
    read -p "Generate test build? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔨 Generating test build (Aetherian Archive)..."
        python3 -m src.eso_build_o_rama.main --trial-id 1
    else
        echo ""
        echo "❌ Cannot run checks without generated output"
        exit 1
    fi
fi

# Step 2: Run deployment check
echo ""
echo "🔍 Running deployment readiness check..."
echo "────────────────────────────────────────────────────────────────"
echo ""

python3 scripts/deployment_check.py "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ❌ CHECK FAILED                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Please fix the issues before merging to main."
    echo ""
    exit 1
fi

# Step 3: Success
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ ALL CHECKS PASSED                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "You can safely merge to main:"
echo ""
echo "  git checkout main"
echo "  git merge $CURRENT_BRANCH"
echo "  git push origin main"
echo ""

exit 0
