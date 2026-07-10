# SO-101 Gripper Sensing Project Summary

## Project Goal

This project is building the sensing and software foundation for an SO-101 robot arm that can detect, grasp, and study objects using multiple sensors.

The planned hardware setup includes:

- 9-zone FSR pressure array on one gripper finger.
- IMU on the other gripper finger for vibration, motion, and temperature-related signals.
- One IMX335 camera mounted near the gripper.
- One fixed IMX335 camera on the table.
- SO-101 arm as the robot platform.

The main software goal is to collect synchronized robot, tactile, IMU, and camera data so the system can later support grasp control, slip detection, object contact analysis, and imitation learning.

## What Has Been Implemented

### ESP32-S3 Firmware

The firmware in `src/main.cpp` was upgraded from a simple FSR monitor into a structured sensing node.

Implemented features:

- Reads all 9 FSR zones.
- Calibrates idle pressure.
- Calibrates max pressure.
- Saves calibration to ESP32 flash using `Preferences`.
- Streams stable `FRAME` packets over serial.
- Adds frame schema version.
- Adds sequence number.
- Adds device timestamp.
- Adds frame delta time.
- Adds reserved IMU fields so the protocol does not need to change later.

Current serial frame format:

```text
FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,
      <raw1>,<pct1>,...,<raw9>,<pct9>,
      <imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
```

The IMU driver is not yet implemented because the exact IMU module has not been confirmed.

### Browser UI

The existing browser monitor in `web-ui/index.html` was updated to understand the new `FRAME` protocol.

It now:

- Displays the 9-zone pressure grid.
- Shows strongest contact point.
- Shows connected sensors.
- Shows frame timing and device time.
- Displays calibration status.
- Remains backward compatible with old `DATA` lines.

### Python Host Parser

A reusable parser was added at `host/so101_sensing/parser.py`.

It parses:

- `STATUS` lines.
- New `FRAME` lines.
- Legacy `DATA` lines.

It also computes useful contact features:

- Total pressure.
- Active sensor count.
- Contact centroid.
- Strongest sensor.

### Dataset Recorder

A recorder tool was added at `tools/record_sensor_log.py`.

It can record live serial data into:

- JSONL for structured robot datasets.
- CSV for quick inspection and plotting.

Example:

```bash
python3 tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

### ROS 2 Bridge Scaffold

A ROS 2 package was added at:

```text
ros2_ws/src/so101_sensing_bridge
```

It provides a bridge node that reads ESP32 serial frames and publishes:

- Full sensor frames as JSON.
- Compact contact features as `Float32MultiArray`.
- Status messages.

This is the first step toward integrating the FSR/IMU data with SO-101 control, cameras, rosbag recording, and future perception/control nodes.

### Documentation

Added documentation:

- `README.md`
- `docs/software_architecture.md`
- `docs/PROJECT_SUMMARY.md`
- `docs/HANDOFF_NEXT_SESSION.md`

## Verification Completed

The firmware build passed:

```bash
/home/enders/.platformio/penv/bin/pio run
```

The parser tests passed:

```bash
python3 -m unittest discover -s test -p 'test_*.py'
```

Python syntax checks passed for the parser, recorder, and ROS bridge.

The ROS 2 package was not fully built because `colcon` is not installed in the current environment.

## Current Limitations

- The exact IMU module is still unknown, so `readImuSample()` is currently a stub.
- Camera capture is not implemented yet.
- SO-101 robot control is not connected yet.
- No synchronized camera plus FSR plus robot-action dataset has been recorded yet.
- The ROS 2 bridge currently uses JSON and standard messages rather than custom ROS messages.

## Recommended Next Direction

The next development stage should focus on:

1. Confirming the exact IMU hardware.
2. Adding the IMU driver to the ESP32 firmware.
3. Connecting both IMX335 cameras to the host computer.
4. Creating a synchronized recording pipeline.
5. Adding SO-101 joint/action logging.
6. Recording real grasping experiments.
7. Building a simple grasp state machine.
8. Later converting successful demonstrations into a LeRobot dataset.
