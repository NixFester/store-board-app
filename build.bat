@echo off
echo ============================================
echo  Azzahra Computer Board -- Build Script
echo ============================================
echo.

REM Install dependencies (run quietly so output doesn't mix with PyInstaller)
echo Installing dependencies...
pip install pillow requests pyinstaller -q
if errorlevel 1 (
    echo [ERROR] pip install failed!
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous build artefacts...
rmdir /s /q build 2>nul
rmdir /s /q dist  2>nul

REM ── Build using the spec file (honours hiddenimports + excludes) ──────────
REM --contents-directory . places python314.dll + all DLLs next to the .exe
REM (PyInstaller 6+).  This fixes "python3xx.dll could not be found" when the
REM exe is launched from any working directory or via double-click.
echo.
echo Running PyInstaller...
python -m PyInstaller --noconfirm azzahra_board.spec
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed! See log above.
    pause
    exit /b 1
)

REM ── Verify exe was actually produced ─────────────────────────────────────
if not exist "dist\azzahra_board\azzahra_board.exe" (
    echo.
    echo [ERROR] Build succeeded but exe not found at dist\azzahra_board\azzahra_board.exe
    echo         Check the PyInstaller output above for warnings.
    pause
    exit /b 1
)

REM ── Copy runtime files into dist ──────────────────────────────────────────
echo.
echo Copying assets, version and config...
xcopy /s /e /y /i "assets"  "dist\azzahra_board\assets"     >nul 2>&1
copy  "version.txt"          "dist\azzahra_board\version.txt" >nul 2>&1
copy  "config.txt"           "dist\azzahra_board\config.txt"  >nul 2>&1

REM ── Create dist.zip for upload ────────────────────────────────────────────
echo.
echo Creating dist.zip...
powershell -NoProfile -Command ^
  "Compress-Archive -Path 'dist\azzahra_board\*' -DestinationPath 'dist\azzahra_board\dist.zip' -Force"
if errorlevel 1 (
    echo [ERROR] Failed to create dist.zip!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE!
echo ============================================
echo.
echo  Executable : dist\azzahra_board\azzahra_board.exe
echo  ZIP file   : dist\azzahra_board\dist.zip
echo.
echo  Upload dist.zip to GitHub Releases or your website.
echo.
pause