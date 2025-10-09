@echo off
REM Build Python backend with Nuitka (Windows)

echo Building AssetForge backend with Nuitka...

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install nuitka ordered-set zstandard

REM Build with Nuitka
echo Compiling with Nuitka...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --output-dir=bin ^
    --output-filename=assetforge_backend.exe ^
    --assume-yes-for-downloads ^
    --enable-plugin=anti-bloat ^
    --nofollow-import-to=pytest,unittest,test ^
    --include-package-data=openai,pydantic ^
    app/main.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Binary: backend\bin\assetforge_backend.exe
) else (
    echo.
    echo Build failed!
    exit /b 1
)

deactivate
cd ..
