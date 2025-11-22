@echo off
REM Build Python backend with Nuitka (Windows)

echo Building AssetFurnace backend with Nuitka...

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

REM Build with Nuitka (standalone mode for debugging)
echo Compiling with Nuitka in STANDALONE mode...
echo This creates a folder with all dependencies visible for debugging.
python -m nuitka ^
    --standalone ^
    --jobs=0 ^
    --output-dir=bin ^
    --assume-yes-for-downloads ^
    --nofollow-import-to=pytest,unittest,test ^
    --include-package=app ^
    --include-package=openai ^
    --include-package=pydantic ^
    --include-package=pydantic_core ^
    --include-package=rich ^
    --include-package=orjson ^
    --include-package=cryptography ^
    --include-package=platformdirs ^
    --include-package=jsonschema ^
    --include-package=dateutil ^
    --include-package=tenacity ^
    --include-data-dir=app/pipeline/agents/prompts=app/pipeline/agents/prompts ^
    --include-data-dir=app/pipeline/agents/asset_agents/prompts=app/pipeline/agents/asset_agents/prompts ^
    --include-data-dir=app/pipeline/agents/schemas=app/pipeline/agents/schemas ^
    --include-data-dir=app/pipeline/agents/asset_agents/schemas=app/pipeline/agents/asset_agents/schemas ^
    --include-data-file=bin/pandoc.exe=bin/pandoc.exe ^
    --include-data-file=bin/wkhtmltopdf/bin/wkhtmltopdf.exe=bin/wkhtmltopdf/bin/wkhtmltopdf.exe ^
    --include-data-file=bin/wkhtmltopdf/bin/wkhtmltoimage.exe=bin/wkhtmltopdf/bin/wkhtmltoimage.exe ^
    --include-data-file=bin/wkhtmltopdf/bin/wkhtmltox.dll=bin/wkhtmltopdf/bin/wkhtmltox.dll ^
    --include-data-file=bin/wkhtmltopdf/bin/vcruntime140.dll=bin/wkhtmltopdf/bin/vcruntime140.dll ^
    --include-data-file=bin/wkhtmltopdf/bin/vcruntime140_1.dll=bin/wkhtmltopdf/bin/vcruntime140_1.dll ^
    --include-data-file=bin/wkhtmltopdf/bin/msvcp140.dll=bin/wkhtmltopdf/bin/msvcp140.dll ^
    --windows-console-mode=disable ^
    app/main.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo.
    echo ========================================
    echo STANDALONE MODE OUTPUT
    echo ========================================
    echo Executable: backend\bin\main.dist\main.exe
    echo DLLs folder: backend\bin\main.dist\
    echo.
    echo To inspect bundled DLLs, check the main.dist folder.
    echo All dependencies should be visible there.
    echo.
    echo To test: cd backend\bin\main.dist ^&^& main.exe
    echo ========================================
    echo.

    REM Don't clean up in standalone mode - we need to inspect the output
    echo ✅ Backend build completed successfully!
) else (
    echo.
    echo Build failed!
    exit /b 1
)

deactivate
cd ..
