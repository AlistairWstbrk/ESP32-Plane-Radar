#!/usr/bin/env bash
# Flash ESP32-Plane-Radar firmware to an ESP32-C3 Super Mini
# Usage: ./flash.sh            (auto-detects port)
#        ./flash.sh /dev/ttyUSB0   (specify port)

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v esptool.py &>/dev/null; then
  echo "esptool.py not found. Install it with:"
  echo "  pip install esptool"
  exit 1
fi

PORT_ARG=""
if [ -n "$1" ]; then
  PORT_ARG="--port $1"
else
  # Try to auto-detect a likely port
  DETECTED=$(ls /dev/cu.usbmodem* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -1)
  if [ -n "$DETECTED" ]; then
    PORT_ARG="--port $DETECTED"
    echo "Using detected port: $DETECTED"
  fi
fi

esptool.py \
  $PORT_ARG \
  --chip esp32c3 \
  --baud 921600 \
  --before default_reset \
  --after hard_reset \
  write_flash \
  --flash_mode dio \
  --flash_freq 80m \
  --flash_size 4MB \
  0x0000  "$DIR/bootloader.bin" \
  0x8000  "$DIR/partitions.bin" \
  0xe000  "$DIR/boot_app0.bin"  \
  0x10000 "$DIR/firmware.bin"

echo ""
echo "Flash complete. The device is rebooting."
