# Flashing ESP32-Plane-Radar

Colour-coded aircraft classification fork of
[MatixYo/ESP32-Plane-Radar](https://github.com/MatixYo/ESP32-Plane-Radar).

## What's different

Aircraft icons and colours now reflect their type:

| Class | Icon | Colour |
|---|---|---|
| Commercial | Fuselage + wing bar + tail fins | Cyan |
| Military | Bold filled triangle | Red-orange |
| Helicopter | Rotor-disk circle + mini heading arrow | Amber |
| Private / GA | Narrow filled triangle | Lime green |

Classification uses the ADS-B emitter category field and known military
ICAO hex address blocks (RAF, USAF, Luftwaffe, RAAF, RCAF).

---

## Requirements

- **ESP32-C3 Super Mini** (the hardware this build targets)
- **Python 3** and **esptool.py**

Install esptool if you don't have it:

```
pip install esptool
```

---

## Mac / Linux

1. Connect the ESP32-C3 via USB.
2. Open a terminal in this `release/` folder.
3. Run:

```bash
chmod +x flash.sh
./flash.sh
```

The script auto-detects the port. If it picks the wrong one, pass it
explicitly:

```bash
./flash.sh /dev/cu.usbmodem1101   # Mac example
./flash.sh /dev/ttyUSB0           # Linux example
```

---

## Windows

1. Connect the ESP32-C3 via USB.
2. Open Device Manager → Ports (COM & LPT) and note the COM number
   (e.g. `COM3`).
3. Double-click `flash.bat`, or run from a terminal:

```
flash.bat COM3
```

---

## Manual esptool command

If the scripts don't work, run this directly (replace `PORT` with your
port, e.g. `/dev/cu.usbmodem1101` or `COM3`):

```
esptool.py \
  --port PORT \
  --chip esp32c3 \
  --baud 921600 \
  write_flash \
  --flash_mode dio --flash_freq 80m --flash_size 4MB \
  0x0000  bootloader.bin \
  0x8000  partitions.bin \
  0xe000  boot_app0.bin  \
  0x10000 firmware.bin
```

---

## Troubleshooting

**"Failed to connect"** — Hold the BOOT button on the board, press and
release RESET, then release BOOT. Run the flash command again within
a few seconds.

**Wrong port / multiple devices** — specify the port explicitly as shown
above.

**Build from source** — open the project root in VS Code with the
PlatformIO extension, or run `pio run -t upload` from the project root.
