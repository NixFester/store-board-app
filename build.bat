@echo off
echo ============================================
echo  Azzahra Computer Board — Build Script
echo ============================================
echo.

REM Install dependencies
pip install pillow requests pyinstaller

REM Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build with PyInstaller (onedir mode for auto-update support)
python -m PyInstaller --noconfirm ^
    --name azzahra_board ^
    --windowed ^
    --onedir ^
    --collect-all PIL ^
    main.py

REM Copy assets and version to dist
echo.
echo Copying assets and version...
xcopy /s /e /y /i "assets" "dist\azzahra_board\assets" >nul 2>&1
copy "version.txt" "dist\azzahra_board\version.txt" >nul 2>&1
copy "config.txt" "dist\azzahra_board\config.txt" >nul 2>&1

echo.
echo ============================================
echo  BUILD COMPLETE!
echo ============================================
echo.
echo  Executable: dist\azzahra_board\azzahra_board.exe
echo  ZIP file:   dist\azzahra_board\dist.zip
echo.
echo  Upload dist.zip to GitHub Releases or your website.
echo.
pause