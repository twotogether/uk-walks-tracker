#!/bin/bash

# One-click build script for UK Walks Tracker (Unix/Linux/macOS)
# This script builds the entire project in one command

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo "  UK Walks Tracker - One-Click Build (Unix/Linux/macOS)"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed or not in PATH"
    exit 1
fi

# Run the build script with arguments
case "${1:-}" in
    "")
        echo "Running standard build..."
        echo ""
        python3 scripts/build.py
        ;;
    "--clean")
        echo "Running clean build..."
        echo ""
        python3 scripts/build.py --clean
        ;;
    "--preview")
        echo "Running build with preview..."
        echo ""
        python3 scripts/build.py --preview
        ;;
    "--help")
        python3 scripts/build.py --help
        ;;
    *)
        echo "Unknown option: $1"
        echo ""
        echo "Usage:"
        echo "  ./build.sh              - Standard build"
        echo "  ./build.sh --clean      - Clean build (removes old artifacts)"
        echo "  ./build.sh --preview    - Build and open in browser"
        echo "  ./build.sh --help       - Show help message"
        echo ""
        exit 1
        ;;
esac

if [ $? -ne 0 ]; then
    echo ""
    echo "Build failed! Check the output above for details."
    exit 1
fi

echo ""
echo "Build completed successfully!"
