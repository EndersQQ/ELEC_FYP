# SO-101 Gripper Sensing Stack

This repository contains the public working parts of an SO-101 gripper sensing and teleoperation project.

## Public Scope

This repo currently includes:

- ESP32-S3 firmware for a 9-zone FSR tactile sensor.
- Host-side Python tools for parsing and recording sensor streams.
- A browser pressure-monitor UI.
- ROS 2 bridge scaffolding for publishing sensor data.
- Camera and dataset tooling for future grasping experiments.

Private lab notes, daily logs, calibration history, hardware troubleshooting notes, and AI handoff details are not kept in the public repository.

## Repository Layout

```text
so-101/
  sensors/fsr9/          ESP32-S3 FSR tactile firmware
  sensors/imu/           IMU integration area
  perception/camera/     Camera setup notes
  control/               Robot control planning area
  software/              Python host tools, package, UI, scripts, and tests
  ros2_ws/               ROS 2 bridge workspace
  docs/                  Public project documentation
  data/                  Local data output area
```

## Firmware

Build the FSR firmware from `so-101/sensors/fsr9`:

```bash
pio run
```

Upload with the correct local serial port for your ESP32-S3 board:

```bash
pio run --target upload --upload-port <sensor-port>
```

The firmware streams structured serial frames for downstream tools:

```text
FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,<raw1>,<pct1>,...,<raw9>,<pct9>,<imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
```

## Host Tools

Python tools live under `so-101/software`.

Run tests:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Record sensor data:

```bash
cd so-101
python software/tools/record_sensor_log.py --port <sensor-port> --format jsonl
```

Start the browser UI:

```bash
cd so-101/software
./scripts/start_ui.sh <sensor-port>
```

Then open:

```text
http://127.0.0.1:8090
```

## Robot Teleoperation

SO-101 leader/follower teleoperation is developed with LeRobot. Local serial device names and calibration values are machine-specific and are intentionally not documented in this public README.

For a local setup, prefer persistent `/dev/serial/by-id/...` paths instead of `/dev/ttyACM*` names, because Linux may reorder `ttyACM` devices after USB replug.

## Public Status

Working public components:

- FSR firmware and serial frame format.
- Host parser and recorder tools.
- Browser pressure monitor.
- ROS 2 bridge scaffold.
- Initial camera/data recording utilities.

Private/internal components:

- Daily lab logs.
- Calibration files and exact local hardware mappings.
- Debugging history and unresolved hardware notes.
- AI handoff notes.
