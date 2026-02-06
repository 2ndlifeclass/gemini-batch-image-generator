#!/bin/bash
echo "Building Gemini Image Generator for macOS..."

# Create virtual environment
python3 -m venv build-env
source build-env/bin/activate

# Install dependencies
pip install -r requirements-gui.txt

# Build executable
pyinstaller --name="GeminiImageGenerator" \
    --onefile \
    --windowed \
    --add-data "README.md:." \
    app.py

echo ""
echo "Build complete! Check the 'dist' folder."
