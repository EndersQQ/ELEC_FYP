# Repository Map

Working project name: **SO-101 Gripper Sensing Stack**

The GitHub repository root should show `so-101/` as the main project folder. Inside it, each major technical area has its own place.

```text
so-101/
  sensors/
    fsr9/
      platformio.ini          PlatformIO firmware config
      src/main.cpp            ESP32-S3 FSR tactile firmware
      scripts/before_upload.py
      scripts/web_ui.sh       Start/stop/status helper for the browser monitor
      web-ui/                 Serial bridge and browser pressure monitor

    imu/
      README.md               IMU hardware/driver integration notes

  perception/
    camera/
      README.md               Camera setup and future dual IMX335 notes

  control/
    README.md                 SO-101 robot control and action logging plan

  software/
    host/so101_sensing/       Reusable Python package
    tools/                    Runnable recording/training tools
    notebooks/                Optional Google Colab entrypoints
    scripts/                  Host setup scripts
    test/                     Python tests
    requirements.txt
    requirements-ml.txt

  ros2_ws/
    src/so101_sensing_bridge/ ROS 2 bridge package

  docs/
    PROJECT_SUMMARY.md
    camera-ml-training.md
    sensor-ml-training.md
    codebase-guide.md
    software-architecture.md

  data/
    README.md                 Documents local data layout
    raw/                      Raw episodes; ignored by Git
    processed/                Trained models; ignored by Git
```

## What Goes Where

- FSR firmware changes go in `sensors/fsr9/`.
- IMU research and driver notes go in `sensors/imu/`.
- Camera setup and IMX335 notes go in `perception/camera/`.
- SO-101 action/control work goes in `control/`.
- Reusable Python code goes in `software/host/`.
- Runnable scripts go in `software/tools/` or `software/scripts/`.
- Recorded data goes in `data/raw/`.
- Trained models go in `data/processed/`.
