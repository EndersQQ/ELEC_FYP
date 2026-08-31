# Codebase Guide

The repository has one main data path:

```text
9 FSR zones + MPU6050
          |
          v
ESP32-S3 firmware -- FRAME lines --> one serial consumer
                                      |-- browser bridge and dashboard
                                      |-- sensor/dataset recorder
                                      `-- ROS 2 bridge
```

Only one serial consumer can open the ESP32 device at a time.

## Firmware and browser monitor

- `sensors/fsr9/platformio.ini` selects the ESP32-S3 Arduino target, serial settings, and upload hook.
- `sensors/fsr9/src/main.cpp` samples all nine FSR channels, filters their ADC readings, calibrates idle values, stores calibration in ESP32 preferences, reads the MPU6050, accepts serial commands, and emits schema-1 `FRAME` lines every 20 ms.
- `sensors/fsr9/scripts/before_upload.py` releases the configured serial port before upload and restarts the dashboard afterward.
- `sensors/fsr9/scripts/web_ui.sh` is the single start, stop, restart, status, and log interface for the dashboard process.
- `sensors/fsr9/web-ui/bridge.py` owns the serial port, serves the static dashboard, forwards serial lines through server-sent events, and sends the `IDLE` calibration command.
- `sensors/fsr9/web-ui/index.html` renders the 3×3 pressure map, pressure chart, strongest sensor, IMU values and temperature warning, and consumes `STATUS`/`FRAME` messages.
- `sensors/fsr9/web-ui/grab-detector.js` turns pressure totals, peaks, and active-sensor counts into a debounced `GRABBING` state with separate enter and release thresholds.
- `sensors/fsr9/tests/grab-detector.test.js` verifies the grab detector's debounce, release, single-sensor, and weak-contact behavior.

Firmware serial commands are intentionally small: `IDLE` recalibrates, `CLEAR` removes saved calibration then recalibrates, `INFO` prints protocol information, and `CALINFO` prints per-sensor calibration.

## Reusable host package

- `software/host/so101_sensing/parser.py` parses schema-1 `FRAME` and `STATUS` lines into immutable objects and derives total pressure, active count, strongest sensor, and contact centroid.
- `software/host/so101_sensing/camera.py` describes cameras, validates camera specifications, opens OpenCV captures, lists video devices, and saves a timestamped snapshot.
- `software/host/so101_sensing/features.py` extracts deterministic FSR spatial/time features and IMU vibration/frequency features from fixed windows.
- `software/host/so101_sensing/dataset.py` discovers labeled episodes and keeps only windows fully covered by one label interval.
- `software/host/so101_sensing/classifier.py` validates versioned joblib artifacts and provides confidence-thresholded predictions.
- `software/host/so101_sensing/grasp_state.py` combines pressure, vibration, impact, and motion into a debounced advisory grasp state.
- `software/host/so101_sensing/__init__.py` exposes the package's public classes and parser helpers.

## Command-line tools

- `software/tools/record_sensor_log.py` records serial frames as JSONL or CSV.
- `software/tools/record_labeled_sensor_episode.py` records sensor frames and interactive manual label intervals into an episode directory.
- `software/tools/build_sensor_dataset.py` builds inspectable windowed feature JSONL from labeled episodes.
- `software/tools/train_fsr_imu_classifier.py` trains FSR, IMU, or fused baselines and validates them with complete episode groups.
- `software/tools/run_sensor_classifier.py` runs live model inference alongside the transparent vibration/grasp-state detector.
- `software/tools/record_multimodal_episode.py` records timestamped frames from one or more cameras and, optionally, the sensor serial stream into one episode folder.
- `software/tools/check_camera.py` lists cameras, captures a test image, or opens a live preview.
- `software/tools/train_contact_baseline.py` pairs camera images with nearby pressure frames and trains a small contact/no-contact logistic-regression baseline.
- `software/tools/check_so101_motors.py` checks whether configured leader and follower Feetech ports can see servo IDs 1–6 with the expected model number.
- `software/scripts/setup_camera_ml_env.sh` creates the Python virtual environment and installs camera/ML dependencies.
- `software/scripts/fix_serial_permissions.sh` adds the current Linux user to the `dialout` group.
- `software/requirements.txt` contains the serial dependency; `requirements-ml.txt` extends it with OpenCV and baseline-training packages; `requirements-lerobot.txt` pins the separate SO-101 control environment.

## Tests

- `software/test/test_parser.py` checks frame parsing, derived pressure features, status messages, and unknown-line handling.
- `software/test/test_camera.py` checks named/unnamed camera specifications and validation errors without opening hardware.
- `software/test/test_features.py` checks pressure geometry, vibration features, sampling rate, and fixed windows.
- `software/test/test_dataset.py` checks episode discovery and full-interval label alignment.
- `software/test/test_classifier.py` checks model artifact compatibility and feature ordering.
- `software/test/test_grasp_state.py` checks debounce, slip, and robot-motion decisions.

## ROS 2 bridge

- `ros2_ws/src/so101_sensing_bridge/so101_sensing_bridge/fsr_imu_bridge.py` reads the serial stream in a worker thread and publishes full JSON frames, compact contact features, and status messages.
- `ros2_ws/src/so101_sensing_bridge/setup.py`, `setup.cfg`, `package.xml`, and `resource/so101_sensing_bridge` define the ROS 2 Python package and console command.
- `ros2_ws/src/so101_sensing_bridge/so101_sensing_bridge/__init__.py` marks the bridge module as a Python package.

## Deliberately removed duplication

The old `software/web-ui/` copy and its three launcher scripts were removed. They implemented the same dashboard but had already drifted behind the firmware-local version. The obsolete `DATA` serial format and undocumented firmware command aliases were also removed; all current producers and consumers use schema-1 `FRAME` messages.
