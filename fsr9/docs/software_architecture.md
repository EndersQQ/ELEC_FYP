# SO-101 Gripper Sensing Software Architecture

This project is now split into four layers:

1. ESP32-S3 firmware
   - Reads the 9-zone FSR array.
   - Keeps idle/max/deadband calibration in flash.
   - Streams stable `FRAME` packets over serial.
   - Reserves IMU fields in the packet schema.

2. Host tools
   - `host/so101_sensing/parser.py` parses `STATUS`, `FRAME`, and legacy `DATA` lines.
   - `tools/record_sensor_log.py` records JSONL or CSV datasets.

3. Browser monitor
   - `web-ui/index.html` visualizes live FSR pressure and understands the new frame schema.

4. ROS 2 bridge
   - `ros2_ws/src/so101_sensing_bridge` publishes the serial stream into ROS 2.
   - Full frames are published as JSON strings.
   - Compact contact features are published as `Float32MultiArray`.

## Serial Frame

```text
FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,
      <raw1>,<pct1>,...,<raw9>,<pct9>,
      <imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
```

Current schema: `1`

`imu_status` is `0` until the real IMU driver is added. The field is present now so log files, ROS topics, and ML datasets do not need to change later.

## Useful Commands

Build firmware:

```bash
/home/enders/.platformio/penv/bin/pio run
```

Upload firmware:

```bash
./scripts/upload_safe.sh /dev/ttyUSB0
```

Start browser UI:

```bash
./scripts/start_ui.sh /dev/ttyUSB0
```

Record JSONL:

```bash
python3 tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

Record CSV for quick analysis:

```bash
python3 tools/record_sensor_log.py --port /dev/ttyUSB0 --format csv
```

Build ROS 2 bridge:

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 run so101_sensing_bridge fsr_imu_bridge --ros-args -p port:=/dev/ttyUSB0
```

## Next Hardware Decision

The firmware has an IMU slot, but the actual driver depends on the module:

- MPU6050/MPU9250 style I2C IMU
- BNO055/BNO085 orientation sensor
- ICM-20948/ICM-42688 family IMU
- another module

Once the exact part is known, add the driver inside `readImuSample()` in `src/main.cpp`.

## Next Software Milestones

1. Add the exact IMU driver.
2. Add camera capture on the host computer, not the ESP32-S3.
3. Record synchronized FSR + IMU + camera + SO-101 joint/action data.
4. Add grasp state machine:
   `approach -> touch -> close -> stabilize -> lift -> slip recovery`.
5. Convert successful demonstrations into a LeRobot dataset.
