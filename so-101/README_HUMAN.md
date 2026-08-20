# SO-101 Human Operator README

This project is the SO-101 gripper sensing and teleoperation workspace. It combines:

- SO-101 leader/follower arm control through LeRobot.
- ESP32-S3 firmware for a 9-zone FSR pressure sensor.
- Reserved IMU fields for future gripper IMU data.
- Host tools for recording sensor/camera data.
- A browser pressure monitor and ROS 2 bridge scaffold.

## Current Working Setup

Run commands from:

```bash
cd /home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9
```

Use the LeRobot virtual environment installed here:

```text
/home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9/.venv_lerobot
```

Do not use `/dev/ttyACM0` or `/dev/ttyACM1` directly for the arms. Those names can swap after unplugging USB.

Use the stable USB paths:

```text
Follower arm: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00
Leader arm:   /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00
FSR board:    /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0
```

Check them with:

```bash
ls -l /dev/serial/by-id
```

## Teleoperation

Use this command:

```bash
.venv_lerobot/bin/lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00 \
  --robot.id=so101_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00 \
  --teleop.id=so101_leader
```

Stop immediately if a joint moves unexpectedly. Power down the arms before changing wiring or calibration.

## Calibration Files

LeRobot stores calibration outside the repo:

```text
Follower: /home/enders/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json
Leader:   /home/enders/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/so101_leader.json
```

The follower gripper direction has already been fixed by setting:

```json
"gripper": {
    "drive_mode": 1
}
```

## Calibrate Leader

```bash
.venv_lerobot/bin/lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00 \
  --teleop.id=so101_leader
```

If asked whether to use the saved calibration or run calibration:

- Press Enter to reuse the saved calibration.
- Type `c` and press Enter to recalibrate.

When recalibrating, move every joint through its intended range. Move the gripper fully open and fully closed.

## Calibrate Follower

```bash
.venv_lerobot/bin/lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00 \
  --robot.id=so101_follower
```

Press Enter to reuse the edited calibration file. Type `c` only when you want a full recalibration.

## ESP32-S3 FSR Firmware

Firmware path:

```text
sensors/fsr9/
```

Build:

```bash
/home/enders/.platformio/penv/bin/pio run
```

Upload:

```bash
./scripts/upload_safe.sh /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0
```

The firmware streams:

```text
FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,<raw1>,<pct1>,...,<raw9>,<pct9>,<imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
```

## FSR Web UI

Start the pressure monitor:

```bash
cd /home/enders/Documents/ELEC_FYP/so-101/software
./scripts/start_ui.sh /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0
```

Open:

```text
http://127.0.0.1:8090
```

## Open Issues

These are not fixed yet:

- Hot IMU: https://github.com/EndersQQ/ELEC_FYP/issues/8
- Follower wrist_roll visual offset: https://github.com/EndersQQ/ELEC_FYP/issues/9

Do not reconnect the IMU if it gets hot within seconds. Check wiring with power off first.
