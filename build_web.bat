@echo off
REM WebAssembly build script for Sipa: Kanto Clicker using Pygbag
echo === Packaging Sipa: Kanto Clicker for WebAssembly ===

if exist "build\web" (
    echo Cleaning previous web build artifacts...
    rmdir /s /q "build\web"
)

echo Running Pygbag compiler...
python -m pygbag --build .

echo.
echo === Build Complete! ===
echo WebAssembly bundle exported to: build\web\
echo To test locally in your browser, run:
echo   python -m pygbag .
echo   and open http://localhost:8000 in your browser.
