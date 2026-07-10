# SO-101 Gripper Sensing Stack

This project collects synchronized SO-101 gripper data for tactile sensing, perception, control, and future imitation learning.

Implemented so far:

- ESP32-S3 firmware for a 9-zone FSR pressure array
- stable serial `FRAME` protocol with reserved IMU fields
- browser pressure monitor
- Python parser and dataset tools
- Logitech/UVC setup camera capture
- starter contact/no-contact ML training pipeline
- ROS 2 bridge scaffold

Planned next areas:

- real IMU driver once hardware is confirmed
- two IMX335 cameras: gripper view and table view
- SO-101 robot action/joint logging
- grasp-state machine
- LeRobot dataset conversion

## Start Here

- Folder map: `docs/repository-map.md`
- Camera training guide: `docs/camera-ml-training.md`
- Current architecture: `docs/software-architecture.md`
- Session handoff: `docs/next-session-handoff.md`
- Development history: `docs/summary-log.md`

Each major folder also has its own `README.md`.

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
