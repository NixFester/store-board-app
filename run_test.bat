@echo off
cd /d "%~dp0"
echo ====================================
echo  Store Board App - Test Launcher
echo ====================================
echo.
echo  1 - Debug Mode (1024x600 window)
echo  2 - Test Mode (1280x720 window)
echo  3 - Full Kiosk Mode (fullscreen)
echo.
set /p choice="Select mode (1/2/3): "

if "%choice%"=="1" goto debug
if "%choice%"=="2" goto test
if "%choice%"=="3" goto kiosk
goto end

:debug
echo [DEBUG] Starting in windowed mode...
python main.py --debug
goto end

:test
echo [TEST] Starting in 1280x720 test mode...
python main.py --test
goto end

:kiosk
echo [KIOSK] Starting in fullscreen mode...
python main.py
goto end

:end
pause
