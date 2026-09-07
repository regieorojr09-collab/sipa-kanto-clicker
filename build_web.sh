#!/bin/bash
# WebAssembly build script for Sipa: Kanto Clicker using Pygbag
set -e

echo "=== Packaging Sipa: Kanto Clicker for WebAssembly ==="

# Clean old build
if [ -d "build/web" ]; then
    echo "Cleaning previous web build artifacts..."
    rm -rf build/web
fi

# Run pygbag compiler
echo "Running Pygbag compiler..."
python3 -m pygbag --build .

echo ""
echo "=== Build Complete! ==="
echo "WebAssembly bundle exported to: build/web/"
echo "To test locally in your browser, run:"
echo "  python3 -m pygbag ."
echo "  and open http://localhost:8000 in your browser."
