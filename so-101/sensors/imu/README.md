# IMU Sensor

The gripper uses an MPU6050 connected to the ESP32-S3 over I2C.

- SDA: GPIO 17
- SCL: GPIO 18
- Addresses checked: `0x68` and `0x69`
- Driver: direct register access in `sensors/fsr9/src/main.cpp`
- Output: acceleration, angular velocity, and temperature in every `FRAME`
