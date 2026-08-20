# SO-101 AI Handoff README

This file is for future AI/Codex sessions. It records operational state, known paths, hardware mapping, fixed issues, and unresolved work.

## Repo And Working Directory

Primary repo:

```text
/home/enders/Documents/ELEC_FYP/so-101
```

Current IDE/workspace root often starts in:

```text
/home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9
```

GitHub repo:

```text
https://github.com/EndersQQ/ELEC_FYP
```

## Important Local State

LeRobot venv:

```text
/home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9/.venv_lerobot
```

LeRobot version installed during bring-up:

```text
0.4.4
```

Important LeRobot commands expected in the venv:

```text
lerobot-find-port
lerobot-calibrate
lerobot-setup-motors
lerobot-teleoperate
```

## Stable Serial Mapping

Do not rely on `/dev/ttyACM0` and `/dev/ttyACM1`; they swapped after USB replug.

Use:

```text
Follower arm: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00
Leader arm:   /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00
FSR board:    /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0
```

Validate with:

```bash
ls -l /dev/serial/by-id
```

## Current Teleop Command

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

## Calibration Files

Follower:

```text
/home/enders/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json
```

Leader:

```text
/home/enders/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/so101_leader.json
```

Known follower gripper fix:

```json
"gripper": {
    "id": 6,
    "drive_mode": 1
}
```

This was written to the follower motors after editing the JSON. Keep this setting unless the physical gripper is rebuilt or recalibrated from scratch.

## Fixed Issues From 2026-08-20

Closed GitHub issues:

- #1 Fix SO-101 leader/follower USB port swap after replug
- #2 Install LeRobot Feetech tooling for SO-101 teleoperation
- #3 Identify SO-101 serial device roles
- #4 Verify SO-101 Feetech motor IDs on both buses
- #5 Recalibrate leader gripper after fixed position reading
- #6 Restore follower gripper response after power reconnect
- #7 Fix reversed follower gripper direction

Relevant local summary:

```text
/home/enders/Documents/ELEC_FYP/so-101/docs/summary-log.md
```

Issue draft source:

```text
/home/enders/Documents/ELEC_FYP/so-101/docs/resolved-github-issues-2026-08-20.md
```

## Open Issues

Open GitHub issues:

- #8 Investigate hot IMU on ESP32-S3 gripper sensor board
- #9 Trim follower wrist_roll alignment offset

Do not mark either fixed until verified.

## Hot IMU Safety Note

The IMU was reported as super hot. Treat this as a hardware safety issue.

Expected wiring from current firmware:

```text
IMU VCC -> 3.3V
IMU GND -> GND
IMU SDA -> ESP32 GPIO17
IMU SCL -> ESP32 GPIO18
```

Do not reconnect the IMU if it heats within seconds. Check VCC/GND/SDA/SCL and shorts with power off first.

Firmware currently initializes MPU6050-compatible I2C at:

```text
SDA GPIO17
SCL GPIO18
I2C 100 kHz
address 0x68 or 0x69
```

## Wrist Roll Remaining Work

Problem:

When leader wrist roll is visually perpendicular, follower wrist roll is slightly left.

Observed diagnostic readings:

```text
leader wrist_roll:   about 6.55 deg
follower wrist_roll: about 6.11 deg
```

Interpretation:

LeRobot normalized values are already close, so this is likely a visual/mechanical zero trim on follower `wrist_roll`, not a mapping failure.

Suggested starting edit in follower calibration:

```text
wrist_roll.homing_offset -= 114
```

Then run follower calibration and press Enter to reuse the file, or write calibration programmatically to the follower motor. Verify visually before closing issue #9.

## FSR Firmware And Sensor Stack

Firmware root:

```text
/home/enders/Documents/ELEC_FYP/so-101/sensors/fsr9
```

Build:

```bash
/home/enders/.platformio/penv/bin/pio run
```

Upload:

```bash
./scripts/upload_safe.sh /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5069RR4-if00-port0
```

Serial frame:

```text
FRAME,<schema>,<seq>,<ms>,<dt_ms>,<connected>,
      <raw1>,<pct1>,...,<raw9>,<pct9>,
      <imu_status>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>,<temp_c>
```

## Caution For Future AI Agents

- Never suggest `/dev/ttyACM0` or `/dev/ttyACM1` as persistent arm ports.
- Do not close hot IMU issue without a physical wiring and temperature verification.
- Do not overwrite LeRobot calibration files casually; back them up first.
- Do not run torque-enabled tests if the user reports uncontrolled motion.
- Use GitHub connector for issues when available; `gh` CLI was not installed during the session.
