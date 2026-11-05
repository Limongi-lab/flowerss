@echo off
setlocal

echo ==========================================================
echo   A Flower For You  –  Build script
echo ==========================================================
echo.

REM ── 1. Install / upgrade dependencies ────────────────────
echo [1/3] Installing Python dependencies...
pip install --upgrade pillow numpy pyinstaller
if errorlevel 1 (
    echo ERROR: pip failed. Make sure Python is in your PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable with PyInstaller...
echo.

pyinstaller ^
    --noconsole ^
    --onefile ^
    --name "AFlowerForYou" ^
    --collect-all PIL ^
    --hidden-import PIL._tkinter_finder ^
    main.py

echo.

REM ── 3. Report result ─────────────────────────────────────
if exist "dist\AFlowerForYou.exe" (
    echo [3/3] SUCCESS!
    echo.
    echo   Your executable is ready at:
    echo   %CD%\dist\AFlowerForYou.exe
    echo.
    echo   You can send this file directly via WhatsApp.
    echo   The recipient just needs to double-click it - no Python required.
) else (
    echo [3/3] Build may have failed. Check the output above for errors.
)

echo.
pause
