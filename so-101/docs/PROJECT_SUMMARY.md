# SO-101 Gripper Sensing Stack

This project collects synchronized SO-101 gripper data for tactile sensing, perception, control, and future imitation learning.

Implemented so far:

- ESP32-S3 firmware for a 9-zone FSR pressure array
- stable serial `FRAME` protocol carrying FSR and MPU6050 samples
- browser pressure monitor with a transparent grab detector
- Python parser and dataset tools
- manually labeled FSR/IMU episode recording
- windowed pressure and vibration feature extraction
- FSR, IMU, or fused scikit-learn classifier training
- live model inference with a debounced grasp/vibration state machine
- Logitech/UVC setup camera capture
- starter contact/no-contact ML training pipeline
- ROS 2 bridge scaffold

Planned next areas:

- two IMX335 cameras: gripper view and table view
- SO-101 robot action/joint logging
- higher-rate IMU recording for vibration frequencies above the current 50 Hz stream
- LeRobot dataset conversion

## Start Here

- Folder map: `docs/repository-map.md`
- Code guide: `docs/codebase-guide.md`
- Camera training guide: `docs/camera-ml-training.md`
- Sensor training guide: `docs/sensor-ml-training.md`
- Current architecture: `docs/software-architecture.md`

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
