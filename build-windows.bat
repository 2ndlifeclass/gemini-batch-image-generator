@echo off
echo Building Gemini Image Generator for Windows...

REM Create virtual environment
python -m venv build-env
call build-env\Scripts\activate.bat

REM Install dependencies
pip install -r requirements-gui.txt

REM Build executable
pyinstaller --name="GeminiImageGenerator" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "README.md;." ^
    app.py

echo.
echo Build complete! Check the 'dist' folder.
pause
