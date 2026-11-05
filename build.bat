@echo off
setlocal

echo ==========================================================
echo   A Flower For You  -  Build script
echo ==========================================================
echo.
echo [1/3] Installing dependencies...
python -m pip install --upgrade pillow numpy pyinstaller

echo.
echo [2/3] Building executable...
echo.

python -m PyInstaller ^
    --noconsole ^
    --onefile ^
    --name "AFlowerForYou" ^
    --collect-all PIL ^
    --hidden-import PIL._tkinter_finder ^
    main.py

echo.

if exist "dist\AFlowerForYou.exe" (
    echo [3/3] SUCCESS!
    echo.
    echo   Executable ready at:
    echo   %CD%\dist\AFlowerForYou.exe
    echo.
    echo   Send this file directly via WhatsApp.
    echo   No Python required - just double-click to run.
) else (
    echo [3/3] Build failed. Check the output above.
)

echo.
pause
