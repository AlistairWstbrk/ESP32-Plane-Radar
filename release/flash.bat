@echo off
REM Flash ESP32-Plane-Radar firmware to an ESP32-C3 Super Mini
REM Usage: flash.bat           (auto-detects COM port from Device Manager)
REM        flash.bat COM3      (specify port)

setlocal
set DIR=%~dp0

where esptool.py >nul 2>&1
if errorlevel 1 (
  echo esptool.py not found. Install it with:
  echo   pip install esptool
  pause
  exit /b 1
)

set PORT=
if not "%1"=="" set PORT=--port %1

esptool.py ^
  %PORT% ^
  --chip esp32c3 ^
  --baud 921600 ^
  --before default_reset ^
  --after hard_reset ^
  write_flash ^
  --flash_mode dio ^
  --flash_freq 80m ^
  --flash_size 4MB ^
  0x0000  "%DIR%bootloader.bin" ^
  0x8000  "%DIR%partitions.bin" ^
  0xe000  "%DIR%boot_app0.bin"  ^
  0x10000 "%DIR%firmware.bin"

echo.
echo Flash complete. The device is rebooting.
pause
