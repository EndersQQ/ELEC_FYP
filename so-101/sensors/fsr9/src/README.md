# Firmware

ESP32-S3 firmware lives here.

- `main.cpp` reads the 9-zone FSR array.
- It streams serial `FRAME` messages for host tools, the browser UI, and ROS.
- IMU fields are reserved in the frame, but the real IMU driver still needs the exact IMU model and wiring.

Build from the project root:

```bash
/home/enders/.platformio/penv/bin/pio run
```
