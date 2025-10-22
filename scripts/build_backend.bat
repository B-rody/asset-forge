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
    --jobs=0 ^
    --windows-dependency-tool=pefile ^
    --onefile-tempdir-spec=%%TEMP%%\assetforge ^
    --output-dir=bin ^
    --output-filename=assetforge_backend.exe ^
    --assume-yes-for-downloads ^
    --enable-plugin=anti-bloat ^
    --nofollow-import-to=pytest,unittest,test ^
    --include-package-data=openai,pydantic ^
    --include-module=cryptography ^
    --include-module=orjson ^
    --include-module=keyring ^
    --include-module=sqlite3 ^
    app/main.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Binary: backend\bin\assetforge_backend.exe

    REM Clean up Nuitka build artifacts to reduce bundle size
    echo Cleaning build artifacts...
    if exist "bin\main.build" rmdir /s /q "bin\main.build"
    if exist "bin\main.dist" rmdir /s /q "bin\main.dist"
    if exist "bin\main.onefile-build" rmdir /s /q "bin\main.onefile-build"
    echo ✅ Backend build completed successfully!
) else (
    echo.
    echo Build failed!
    exit /b 1
)

deactivate
cd ..
