@echo off
REM Run Python backend in development mode (Windows)

echo Starting AssetForge backend (dev mode)...

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run backend
python app/main.py

deactivate
cd ..
