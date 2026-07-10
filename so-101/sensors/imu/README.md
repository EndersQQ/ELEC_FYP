# IMU Sensor

This folder is reserved for the gripper IMU integration.

Current status:

- The ESP32 serial `FRAME` schema already includes IMU fields.
- `sensors/fsr9/src/main.cpp` still returns a stub IMU sample.
- The real driver depends on the exact IMU model, bus type, and pin wiring.

Next implementation steps:

1. Confirm IMU model.
2. Confirm I2C or SPI wiring.
3. Add the PlatformIO library under `sensors/fsr9/platformio.ini`.
4. Replace the `readImuSample()` stub in `sensors/fsr9/src/main.cpp`.
