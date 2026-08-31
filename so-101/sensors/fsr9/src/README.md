# Firmware

ESP32-S3 firmware lives here.

- `main.cpp` reads the 9-zone FSR array.
- It streams serial `FRAME` messages for host tools, the browser UI, and ROS.
- `main.cpp` reads an MPU6050 IMU on SDA 17 and SCL 18 when it is available.
- The web UI shows a live 3x3 pressure map, a nine-sensor bar graph, and a
  pressure-based `GRABBING` / `NOT GRABBING` estimate.

## Simple grabbing detector

The first detector is deliberately a transparent baseline rather than a trained
model. It uses the calibrated pressure percentages already sent by the firmware:

```text
9 calibrated FSR percentages
            |
            v
 total pressure + peak pressure + number of active sensors
            |
            v
 hysteresis and short time debounce
            |
            v
      GRABBING / NOT GRABBING
```

It enters `GRABBING` after five consecutive frames when either one sensor is at
least 25%, or at least two sensors together total 25%. It returns to
`NOT GRABBING` after ten consecutive low-pressure frames. The different enter
and release thresholds prevent flicker near the boundary. Thresholds are kept
in `web-ui/grab-detector.js` so they can be tuned from recorded hardware data.

This detects pressure contact; without the gripper motor position it cannot
distinguish a closed grasp from someone pressing the sensor by hand.

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
