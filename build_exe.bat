@echo off
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt pyinstaller || goto :error
python -m PyInstaller --noconfirm --clean --onefile --windowed --name HeartRateOverlay --collect-submodules winrt --collect-submodules bleak main.py || goto :error

echo.
echo Build complete: dist\HeartRateOverlay.exe
exit /b 0

:error
echo.
echo Build failed. Check the messages above.
exit /b 1
