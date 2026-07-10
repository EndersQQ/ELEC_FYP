# FSR 9 Array SO-101 Gripper Sensor Stack

This project contains the first long-term software stack for the SO-101 gripper sensing setup:

- ESP32-S3 firmware for the 9-zone FSR array.
- Stable serial `FRAME` packets with timestamps, sequence numbers, calibration, FSR pressure, and reserved IMU fields.
- Browser UI for live pressure visualization.
- Python parser and recorder for dataset collection.
- ROS 2 bridge scaffold for robot integration.

Start here:

- Architecture notes: `docs/software_architecture.md`
- Summary log: `docs/summary-log.md`
- Next-session handoff: `docs/next-session-handoff.md`
- GitHub workflow: `docs/github-workflow.md`
- Firmware: `src/main.cpp`
- Parser: `host/so101_sensing/parser.py`
- Recorder: `tools/record_sensor_log.py`
- ROS 2 bridge: `ros2_ws/src/so101_sensing_bridge`

Build firmware:

```bash
/home/enders/.platformio/penv/bin/pio run
```

Run tests:

```bash
python3 -m unittest discover -s test -p 'test_*.py'
```
