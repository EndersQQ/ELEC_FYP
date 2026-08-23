# Firmware

ESP32-S3 firmware lives here.

- `main.cpp` reads the 9-zone FSR array.
- It streams serial `FRAME` messages for host tools, the browser UI, and ROS.
- IMU fields are reserved in the frame, but the real IMU driver still needs the exact IMU model and wiring.

The FSR divider is wired so pressure raises the ADC reading:

```text
3.3V -> sensor C/common -> FSR point -> ADC pin -> resistor -> GND
```

After changing wiring or flashing firmware with a new calibration version, leave
all sensors released during automatic idle calibration. The calibrated idle raw
value is 0% pressure, and raw 4095 is the fixed 100% pressure endpoint.

Build from the project root:

```bash
/home/enders/.platformio/penv/bin/pio run
```

Upload from the project root to flash the ESP32-S3 and restart the local web UI bridge:

```bash
/home/enders/.platformio/penv/bin/pio run --target upload
```

Then open:

```text
http://127.0.0.1:8090
```

To start, check, or stop the web UI bridge manually:

```bash
./scripts/web_ui.sh start /dev/ttyUSB0
./scripts/web_ui.sh status
./scripts/web_ui.sh log
./scripts/web_ui.sh stop
```
