# SO-101 Gripper Sensing Software Architecture

The project is split by technical purpose:

1. FSR tactile firmware: `sensors/fsr9/`
   - ESP32-S3 PlatformIO project.
   - Reads the 9-zone FSR array.
   - Keeps idle/max/deadband calibration in flash.
   - Streams stable `FRAME` packets over serial.
   - Reserves IMU fields in the packet schema.

2. IMU integration: `sensors/imu/`
   - Holds notes and future driver work.
   - The active firmware stub is still in `sensors/fsr9/src/main.cpp`.

3. Camera perception: `perception/camera/`
   - Documents the temporary Logitech/UVC setup camera.
   - Documents the planned dual IMX335 camera setup.

4. Robot control: `control/`
   - Reserved for SO-101 control, joint/action logging, and later LeRobot work.

5. Host software: `software/`
   - `host/so101_sensing/parser.py` parses `STATUS`, `FRAME`, and legacy `DATA` lines.
   - `host/so101_sensing/camera.py` opens host-connected UVC/IMX335 cameras.
   - `tools/record_sensor_log.py` records JSONL or CSV sensor logs.
   - `tools/record_multimodal_episode.py` records camera frames plus optional FSR/IMU serial data.
   - `tools/train_contact_baseline.py` trains a small camera-to-contact baseline.
   - `web-ui/` contains the browser pressure monitor.

6. ROS 2 bridge: `ros2_ws/`
   - `ros2_ws/src/so101_sensing_bridge` publishes the serial stream into ROS 2.
   - Full frames are published as JSON strings.
   - Compact contact features are published as `Float32MultiArray`.

7. Local data: `data/`
   - `data/raw/` stores raw camera/sensor episodes.
   - `data/processed/` stores trained models and processed datasets.

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
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Upload firmware:

```bash
cd so-101/sensors/fsr9
./scripts/upload_safe.sh /dev/ttyUSB0
```

Run Python tests:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Start browser UI:

```bash
cd so-101/software
./scripts/start_ui.sh /dev/ttyUSB0
```

Record sensor JSONL:

```bash
cd so-101
python software/tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

Set up camera/ML tools:

```bash
cd so-101
./software/scripts/setup_camera_ml_env.sh
source software/.venv/bin/activate
python software/tools/check_camera.py --list
python software/tools/record_multimodal_episode.py --camera setup=/dev/video0 --serial-port /dev/ttyUSB0 --duration 20
```

Build ROS 2 bridge:

```bash
cd so-101/ros2_ws
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

Once the exact part is known, add the driver inside `readImuSample()` in `sensors/fsr9/src/main.cpp`.
