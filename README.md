# ELEC_FYP

Final-year project repository for an SO-101 robotic gripper sensing stack.

The current work focuses on combining tactile sensing, IMU data, camera perception, and robot control so the SO-101 arm can detect contact, understand grasp quality, and eventually learn object-grasping behavior from recorded demonstrations.

## Current Modules

### FSR9 Gripper Sensor Stack

Location:

```text
fsr9/
```

Includes:

- ESP32-S3 firmware for a 9-zone FSR pressure array.
- Structured serial `FRAME` packets with timestamps, sequence numbers, pressure values, and reserved IMU fields.
- Browser UI for live pressure visualization.
- Python parser and dataset recorder.
- ROS 2 bridge scaffold.
- Project summary and handoff documents.

Start here:

- [FSR9 README](fsr9/README.md)
- [Software architecture](fsr9/docs/software_architecture.md)
- [Summary log](fsr9/docs/summary-log.md)
- [Next-session handoff](fsr9/docs/next-session-handoff.md)
- [GitHub workflow](fsr9/docs/github-workflow.md)

## Hardware Direction

Planned system:

- SO-101 robotic arm.
- RF-PUL9Z-V1 3x3 FSR array.
- MPU6050 or equivalent IMU, exact integration still to be finalized.
- ESP32-S3 microcontroller.
- Two IMX335 cameras:
  - one mounted near the gripper,
  - one fixed on the table.

## Software Direction

The target software stack is:

- PlatformIO for ESP32-S3 firmware.
- Python tools for parsing, logging, and experiment utilities.
- ROS 2 for robot/sensor integration.
- LeRobot for SO-101 data collection and imitation learning experiments.
- OpenCV/GStreamer for camera capture.

## Repository Workflow

Use `main` for stable work. Use topic branches for active changes:

```text
feature/imu-driver
feature/camera-capture
feature/ros2-recording
docs/update-handoff
experiment/grasp-dataset-v1
```

Before merging or pushing important changes, run:

```bash
cd fsr9
/home/enders/.platformio/penv/bin/pio run
python3 -m unittest discover -s test -p 'test_*.py'
```

## Status

The first FSR9 software stack has been implemented and tested locally. The next major milestone is adding the real IMU driver and recording synchronized grasping episodes.
