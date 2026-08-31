# SO-101 Gripper Sensing Software Architecture

The project is split by technical purpose:

1. FSR tactile firmware: `sensors/fsr9/`
   - ESP32-S3 PlatformIO project.
   - Reads the 9-zone FSR array.
   - Keeps idle/deadband calibration in flash.
   - Streams stable `FRAME` packets over serial.
   - Reads an MPU6050 over I2C and includes it in each packet.
   - Hosts the single browser pressure-monitor implementation.

2. IMU integration: `sensors/imu/`
   - Documents the active MPU6050 wiring and driver location.

3. Camera perception: `perception/camera/`
   - Documents the temporary Logitech/UVC setup camera.
   - Documents the planned dual IMX335 camera setup.

4. Robot control: `control/`
   - Reserved for SO-101 control, joint/action logging, and later LeRobot work.

5. Host software: `software/`
   - `host/so101_sensing/parser.py` parses `STATUS` and schema-1 `FRAME` lines.
   - `host/so101_sensing/camera.py` opens host-connected UVC/IMX335 cameras.
   - `host/so101_sensing/features.py` extracts stable windowed FSR/IMU features.
   - `host/so101_sensing/dataset.py` aligns manual label intervals with complete feature windows.
   - `host/so101_sensing/classifier.py` validates model artifacts and runs predictions.
   - `host/so101_sensing/grasp_state.py` detects vibration and fuses it with pressure state.
   - `tools/record_sensor_log.py` records JSONL or CSV sensor logs.
   - `tools/record_labeled_sensor_episode.py` records interactive label intervals with sensor frames.
   - `tools/build_sensor_dataset.py` materializes inspectable feature JSONL.
   - `tools/train_fsr_imu_classifier.py` trains FSR, IMU, or fused models with episode-level validation.
   - `tools/run_sensor_classifier.py` runs live model and transparent grasp-state inference.
   - `tools/record_multimodal_episode.py` records camera frames plus optional FSR/IMU serial data.
   - `tools/train_contact_baseline.py` trains a small camera-to-contact baseline.
   - The browser UI lives beside its firmware in `sensors/fsr9/web-ui/`.

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

`imu_status` is `1` when an MPU6050 sample is available and `0` when the sensor is absent or a read fails.

## Useful Commands

Build firmware:

```bash
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Upload firmware:

```bash
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run --target upload
```

Run Python tests:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Start browser UI:

```bash
cd so-101/sensors/fsr9
./scripts/web_ui.sh start /dev/ttyUSB0
```

Record sensor JSONL:

```bash
cd so-101
python software/tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

Record labels, train, and run the sensor classifier:

```bash
cd so-101
python software/tools/record_labeled_sensor_episode.py --port /dev/ttyUSB0
python software/tools/train_fsr_imu_classifier.py data/raw --modality fsr
python software/tools/run_sensor_classifier.py --port /dev/ttyUSB0 --model data/processed/fsr_classifier.joblib
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

The browser UI and ROS bridge are alternative serial consumers. Only one process can own the serial port at a time.
