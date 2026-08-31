# ELEC_FYP

Final-year project repository for an **SO-101 robotic gripper sensing and learning stack**.

The goal is to collect synchronized tactile, IMU, camera, and robot-control data so the SO-101 arm can study contact, grasp quality, slip, and eventually learn grasping behavior from demonstrations.

## Repository Layout

```text
so-101/
  sensors/
    fsr9/                 ESP32-S3 PlatformIO project for the 9-zone FSR tactile array
    imu/                  MPU6050 integration notes

  perception/
    camera/               Logitech/UVC setup camera and future dual IMX335 camera plan

  control/                SO-101 robot control, action logging, and future LeRobot work

  software/
    host/                 Reusable Python package for parsing sensor frames and camera helpers
    tools/                Dataset recording, camera checks, and baseline ML training scripts
    scripts/              Host-side setup helpers
    test/                 Python unit tests

  ros2_ws/                ROS 2 bridge workspace
  docs/                   Project summaries, architecture, handoff, and training guides
  data/                   Local experiment outputs; raw data and trained models are ignored by Git
```

## Start Here

- [Project summary](so-101/docs/PROJECT_SUMMARY.md)
- [Repository map](so-101/docs/repository-map.md)
- [Codebase guide](so-101/docs/codebase-guide.md)
- [Camera ML training guide](so-101/docs/camera-ml-training.md)
- [FSR and IMU training guide](so-101/docs/sensor-ml-training.md)
- [Software architecture](so-101/docs/software-architecture.md)

## Common Commands

Build the FSR9 firmware:

```bash
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Run Python tests:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Set up camera/ML tools:

```bash
cd so-101
./software/scripts/setup_camera_ml_env.sh
source software/.venv/bin/activate
```

Activate the SO-101/LeRobot control environment:

```bash
source so-101/.venv_lerobot/bin/activate
```

Record one camera plus FSR episode:

```bash
python software/tools/record_multimodal_episode.py \
  --camera setup=/dev/video0 \
  --serial-port /dev/ttyUSB0 \
  --duration 30
```

Train the starter contact/no-contact model:

```bash
python software/tools/train_contact_baseline.py data/raw --camera setup
```

Record labels and train the FSR classifier:

```bash
python software/tools/record_labeled_sensor_episode.py --port /dev/ttyUSB0
python software/tools/train_fsr_imu_classifier.py data/raw --modality fsr
```

Start the pressure monitor:

```bash
cd so-101/sensors/fsr9
./scripts/web_ui.sh start /dev/ttyUSB0
```

## Branch Policy

This repository should use **one stable branch: `main`**.

Temporary branches can be used locally while developing, but GitHub should only keep `main` unless a separate branch is intentionally needed for review.
