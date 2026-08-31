# SO-101 Gripper Sensing Stack

This folder contains the SO-101 sensing, perception, control, and training work.

## Folder Layout

```text
sensors/fsr9/          ESP32-S3 firmware for the 9-zone FSR tactile array
sensors/imu/           MPU6050 integration notes
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
- `docs/sensor-ml-training.md`
- `docs/software-architecture.md`
- `docs/codebase-guide.md`

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

## FSR and IMU Classification

```bash
python software/tools/record_labeled_sensor_episode.py --port /dev/ttyUSB0
python software/tools/train_fsr_imu_classifier.py data/raw --modality fsr
python software/tools/run_sensor_classifier.py --port /dev/ttyUSB0 --model data/processed/fsr_classifier.joblib
```

See `docs/sensor-ml-training.md` for label definitions, data-collection guidance, Colab use, and evaluation details.
