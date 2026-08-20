# Resolved GitHub Issue Drafts - 2026-08-20

These are GitHub-ready issue drafts for the SO-101 leader/follower bring-up issues fixed during the 2026-08-20 hardware session.

The GitHub connector could not create issues from this session because GitHub returned `403 Resource not accessible by integration`.

## 1. Fix SO-101 Leader/Follower USB Port Swap After Replug

Status: fixed

Problem:

After unplugging and reconnecting the SO-101 USB controllers, Linux reassigned `/dev/ttyACM0` and `/dev/ttyACM1`. Teleoperation could then apply the wrong role/calibration to the wrong arm, causing unsafe wrist motion.

Fix:

Use stable `/dev/serial/by-id/...` paths instead of `/dev/ttyACM*` names.

Stable mapping:

```text
Follower: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00
Leader:   /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00
```

Fixed teleop command:

```bash
.venv_lerobot/bin/lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00 \
  --robot.id=so101_follower \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00 \
  --teleop.id=so101_leader
```

Close reason:

Fixed by switching teleoperation commands to stable serial-by-id device paths and verifying the replugged mapping.

## 2. Install LeRobot Feetech Tooling for SO-101 Teleoperation

Status: fixed

Problem:

The local environment did not have LeRobot commands installed, so `lerobot-calibrate`, `lerobot-teleoperate`, `lerobot-find-port`, and `lerobot-setup-motors` were unavailable.

Fix:

Created a Python 3.10 virtual environment at `sensors/fsr9/.venv_lerobot` and installed LeRobot 0.4.4 with Feetech servo support.

Verified commands:

```text
lerobot-find-port
lerobot-calibrate
lerobot-setup-motors
lerobot-teleoperate
```

Close reason:

Fixed by installing LeRobot and verifying the required SO-101/Feetech command-line tools.

## 3. Identify SO-101 Serial Device Roles

Status: fixed

Problem:

The active USB devices had to be mapped before leader/follower calibration could be run safely.

Fix:

Confirmed device roles:

```text
/dev/ttyACM0 and /dev/ttyACM1: SO-101 motor buses
/dev/ttyUSB0: ESP32-S3 FSR/IMU sensor stream
```

After stable path verification:

```text
Follower: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013655-if00
Leader:   /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B7B013954-if00
```

Close reason:

Fixed by identifying both motor buses and moving to persistent `/dev/serial/by-id` paths.

## 4. Verify SO-101 Feetech Motor IDs on Both Buses

Status: fixed

Problem:

The follower gripper and wrist were suspected missing because an initial connection check missed IDs 5 and 6 on one bus.

Fix:

Ran a direct Feetech broadcast scan and confirmed both SO-101 buses could see motor IDs 1-6:

```text
{1: 777, 2: 777, 3: 777, 4: 777, 5: 777, 6: 777}
```

Close reason:

Fixed by confirming both SO-101 arms expose the full six-motor ID set.

## 5. Recalibrate Leader Gripper After Fixed Position Reading

Status: fixed

Problem:

The follower gripper opened to a fixed target and ignored the leader gripper. Live reads showed the leader gripper stayed at a constant value, so LeRobot was not seeing leader gripper movement.

Fix:

Recalibrated the leader arm with:

```bash
.venv_lerobot/bin/lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM1 \
  --teleop.id=so101_leader
```

During calibration, the leader gripper was moved through its full open/close range.

Close reason:

Fixed by recalibrating the leader gripper so LeRobot reads live gripper movement again.

## 6. Restore Follower Gripper Response After Power Reconnect

Status: fixed

Problem:

The follower gripper did not open/close correctly during teleoperation.

Fix:

After reconnecting follower power and recalibrating the leader, the follower gripper began responding to leader commands again.

Close reason:

Fixed by power-cycling/reconnecting the follower and resolving the leader gripper calibration problem.

## 7. Fix Reversed Follower Gripper Direction

Status: fixed

Problem:

The follower gripper moved in the opposite direction from the leader gripper: leader close caused follower open, and leader open caused follower close.

Fix:

Set only the follower `gripper.drive_mode` to `1` in:

```text
/home/enders/.cache/huggingface/lerobot/calibration/robots/so_follower/so101_follower.json
```

Then wrote the updated calibration back to the follower motors.

Close reason:

Fixed by inverting only the follower gripper normalization direction through `drive_mode = 1`.
