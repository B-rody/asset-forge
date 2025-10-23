@echo off
REM Test the compiled backend binary to ensure it starts properly

echo ============================================
echo AssetForge Backend Diagnostic Test
echo ============================================
echo.

set BACKEND_BIN=backend\bin\assetforge_backend.exe

if not exist "%BACKEND_BIN%" (
    echo ❌ ERROR: Backend binary not found at %BACKEND_BIN%
    echo Please build the backend first using: scripts\build_backend.bat
    exit /b 1
)

echo ✓ Found backend binary: %BACKEND_BIN%
echo.

REM Test 1: Check if binary can start at all
echo [Test 1] Checking if binary starts...
echo.

REM Create a temporary test file with a command
echo {"cmd":"get_api_key"} > test_input.tmp

REM Try to run the binary with verbose output
echo Running: %BACKEND_BIN% ^< test_input.tmp
echo ----------------------------------------
"%BACKEND_BIN%" < test_input.tmp 2>&1

set EXIT_CODE=%errorlevel%
del test_input.tmp

echo ----------------------------------------
echo.

if %EXIT_CODE% equ 0 (
    echo ✅ Test PASSED: Backend started and processed command
    echo    Exit code: %EXIT_CODE%
    echo.
    echo The backend binary is working correctly!
    exit /b 0
) else (
    echo ❌ Test FAILED: Backend crashed or returned error
    echo    Exit code: %EXIT_CODE%
    echo.
    echo Common exit codes:
    echo   -1073741515 (0xC0000135): Missing DLL dependency
    echo   1: Python import error or initialization failure
    echo   3221225477 (0xC0000005): Access violation / segfault
    echo.
    echo Debugging steps:
    echo 1. Check stderr output above for import errors
    echo 2. Verify all dependencies are in Nuitka build
    echo 3. Try running: python backend/app/main.py
    echo 4. Compare working source vs compiled binary
    echo.

    REM Additional diagnostic: Try to get more info with Python dependency checker
    echo.
    echo [Additional Diagnostic] Checking Python dependencies...
    echo Running: python -m pip list ^| findstr "rich openai pydantic"
    python -m pip list | findstr "rich openai pydantic orjson cryptography keyring platformdirs"
    echo.

    exit /b 1
)
