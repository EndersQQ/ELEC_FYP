# SO-101 Gripper Sensing Summary Log

Use this file as the rolling summary of major project updates. Add the newest update near the top when the project changes.

## 2026-08-20 SO-101 Leader/Follower Bring-Up

Enabled and debugged the SO-101 leader/follower teleoperation path using LeRobot.

Completed:

- Installed LeRobot 0.4.4 with Feetech support in `sensors/fsr9/.venv_lerobot`.
- Confirmed serial device roles:
  - `/dev/ttyACM0` is the SO-101 follower motor bus.
  - `/dev/ttyACM1` is the SO-101 leader motor bus.
  - `/dev/ttyUSB0` is the ESP32-S3 FSR/IMU sensor stream.
- Verified both SO-101 buses can see Feetech motor IDs 1-6.
- Recalibrated the leader arm after the leader gripper initially reported a fixed position.
- Restored follower gripper response after reconnecting follower power.
- Fixed reversed follower gripper direction by setting follower `gripper.drive_mode` to `1` in the LeRobot calibration file and writing it to the follower motors.
- Fixed unsafe leader/follower role swaps after USB replug by switching teleoperation commands from `/dev/ttyACM*` names to stable `/dev/serial/by-id/...` paths.

Relevant calibration files:

```text
/home/enders/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json
/home/enders/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/so101_leader.json
```

Current teleoperation command:

```bash
cd /home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9
.venv_lerobot/bin/lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00 \
  --robot.id=so101_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00 \
  --teleop.id=so101_leader
```

Remaining trim:

- Follower `wrist_roll` is slightly left when the leader wrist is visually perpendicular.
- This appears to be a small follower mechanical zero/offset trim, not a mapping failure; live readings showed leader and follower wrist-roll values were very close.
- Suggested adjustment is to reduce follower `wrist_roll.homing_offset` by about `114` ticks in `so101_follower.json`, then write the edited calibration back to the follower motors by running follower calibration and pressing Enter to reuse the file.

## 2026-07-10 Repository Reorganization

Reorganized the GitHub-facing repository from a top-level `fsr9/` folder into a professional SO-101 project layout:

```text
so-101/
  sensors/fsr9/
  sensors/imu/
  perception/camera/
  control/
  software/
  ros2_ws/
  docs/
  data/
```

Updated root `README.md`, `CONTRIBUTING.md`, project docs, scripts, Python tool paths, and training commands to match the new layout.

## 2026-07-10 Camera and ML Starter Stack

Added a host-side camera/ML starter layer for initial SO-101 setup work.

Implemented:

- Optional camera/ML dependencies in `requirements-ml.txt`.
- `scripts/setup_camera_ml_env.sh` to create `.venv` and install OpenCV, NumPy, scikit-learn, joblib, and pyserial.
- `host/so101_sensing/camera.py` for camera configs, `/dev/video*` listing, OpenCV capture, and snapshots.
- `tools/check_camera.py` for listing devices, capturing a test image, or opening preview.
- `tools/record_multimodal_episode.py` for recording one setup camera now or two named cameras later, with optional ESP32 FSR/IMU serial data.
- `tools/train_contact_baseline.py` for a tiny contact/no-contact baseline trained from recorded camera frames paired with nearest FSR frames.
- `docs/camera-ml-training.md` with setup, recording, future dual-IMX335, and baseline-training commands.

The camera path is host-side only. The temporary Logitech/UVC camera can use `setup=/dev/video0`; the final IMX335 pair should use named cameras such as `gripper` and `table`.

Verification completed:

- Parser/camera tests passed with `python3 -m unittest discover -s test -p 'test_*.py'`.
- Python syntax checks passed for host tools, web bridge, and ROS bridge.
- PlatformIO firmware build still passed.
- Camera/ML `.venv` is created in `so-101/software/.venv`.
- `/dev/video0` snapshot succeeded and a 2-second camera-only episode recorded 4 frames.

## 2026-07-10 Initial Software Stack

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
- `docs/software-architecture.md`
- `docs/summary-log.md`
- `docs/next-session-handoff.md`

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
