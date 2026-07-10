# SO-101 Gripper Sensing Stack

This folder contains the SO-101 sensing, perception, control, and training work.

## Folder Layout

```text
sensors/fsr9/          ESP32-S3 firmware for the 9-zone FSR tactile array
sensors/imu/           IMU integration area
perception/camera/     Camera setup, IMX335 planning, and camera-training notes
control/               SO-101 control and action logging area
software/              Python host package, tools, web UI, scripts, and tests
ros2_ws/               ROS 2 bridge workspace
docs/                  Project docs and handoff notes
data/                  Local raw episodes and processed ML outputs
```

## Important Docs

- `docs/PROJECT_SUMMARY.md`
- `docs/repository-map.md`
- `docs/camera-ml-training.md`
- `docs/software-architecture.md`
- `docs/next-session-handoff.md`

## Data Locations

Raw camera/sensor episodes:

```text
data/raw/episode_YYYYMMDD_HHMMSS/
```

Camera test snapshots:

```text
data/raw/camera_checks/
```

Trained baseline models:

```text
data/processed/
```
