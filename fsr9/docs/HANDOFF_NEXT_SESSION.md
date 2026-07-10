# Handoff For Next Session

## Current Project Location

Main project folder:

```text
/home/enders/Documents/PlatformIO/Projects/fsr9
```

Important files:

```text
src/main.cpp
platformio.ini
web-ui/index.html
web-ui/bridge.py
host/so101_sensing/parser.py
tools/record_sensor_log.py
ros2_ws/src/so101_sensing_bridge
docs/software_architecture.md
```

## Current System State

The project now has a first structured software stack for the SO-101 gripper sensing setup.

The ESP32-S3 firmware reads the 9-zone FSR array and streams structured serial `FRAME` messages. Calibration is saved in flash. The browser UI can visualize live pressure data. Python host tools can parse and record data. A ROS 2 bridge scaffold exists.

The IMU fields are already included in the serial frame, but the real IMU driver is not implemented yet because the exact IMU module is not known.

## Verified Commands

Firmware build:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Parser tests:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
python3 -m unittest discover -s test -p 'test_*.py'
```

Both passed during the previous session.

## Useful Run Commands

Upload firmware:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
./scripts/upload_safe.sh /dev/ttyUSB0
```

Start browser UI:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
./scripts/start_ui.sh /dev/ttyUSB0
```

Open:

```text
http://127.0.0.1:8090
```

Record JSONL:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
python3 tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

Record CSV:

```bash
cd /home/enders/Documents/PlatformIO/Projects/fsr9
python3 tools/record_sensor_log.py --port /dev/ttyUSB0 --format csv
```

## Next Questions To Ask User

Ask these before implementing the next hardware-specific stage:

1. What exact IMU module is being used?
2. Is the IMU connected by I2C or SPI?
3. Which ESP32-S3 pins are used for the IMU?
4. How are the two IMX335 cameras connected to the host computer?
5. What OS and computer will run the camera and ROS stack?
6. Is ROS 2 installed? If yes, which distro?
7. Is LeRobot already installed for SO-101?

## Recommended Next Implementation Step

The best next implementation step is to add the real IMU driver.

Work plan:

1. Confirm IMU model and wiring.
2. Add the required PlatformIO library to `platformio.ini`.
3. Initialize the IMU in `setup()`.
4. Replace the `readImuSample()` stub in `src/main.cpp`.
5. Verify serial `FRAME` lines show `imu_status=1`.
6. Update parser tests with real IMU field expectations if needed.
7. Record a short JSONL log with FSR plus IMU data.

## After IMU Works

The next major step should be synchronized camera and robot data recording.

Suggested architecture:

- ESP32-S3 publishes FSR plus IMU serial frames.
- Host Python process reads ESP32 serial data.
- Host captures both IMX335 camera streams.
- SO-101 software logs joint state and gripper action.
- All data is timestamped and saved into one experiment folder.

Recommended experiment folder format:

```text
data/raw/episode_YYYYMMDD_HHMMSS/
  sensor.jsonl
  camera_gripper/
  camera_table/
  robot_actions.jsonl
  metadata.json
```

## Important Notes

- Do not route the IMX335 cameras through the ESP32-S3. They should connect to the host computer.
- The IMU chip temperature usually measures board/chip temperature, not true object temperature.
- If true object temperature is required, add a contact thermistor, digital temperature sensor, or IR temperature sensor near the gripper pad.
- The FSR array provides a contact-pressure map, not a full object shape. Shape estimation should combine FSR data with camera images and robot pose.

## Good First Goal Next Time

Get one clean recorded episode:

1. ESP32-S3 streaming valid FSR frames.
2. IMU fields active.
3. Browser UI showing pressure.
4. Recorder saving JSONL.
5. Manual object grasp performed.
6. Log file reviewed for pressure, centroid, and vibration changes.

That episode becomes the reference dataset for the next stage.
