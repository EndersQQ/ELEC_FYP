# SO-101 Calibration Notes

These notes capture LeRobot calibration checks for an SO-101 leader/follower
setup.

## Active Calibration IDs

LeRobot selects calibration files by device type and `id`.

- Follower calibration files are stored under the LeRobot calibration cache for
  `robots/so_follower/`.
- Leader calibration files are stored under the LeRobot calibration cache for
  `teleoperators/so_leader/`.
- The JSON filename is derived from the `--robot.id` or `--teleop.id` value.

Editing a different id's JSON file will not affect calibration or
teleoperation runs.

## Follower Wrist Roll

Minor follower `wrist_roll` tuning is handled by editing
`wrist_roll.homing_offset` in the active follower calibration file, then
writing that calibration back to the motors with `lerobot-calibrate`.

## Follower Gripper Direction

If the leader and follower grippers move in opposite directions, flip the
follower gripper normalization by setting:

```json
"gripper": {
    "drive_mode": 1
}
```

For the gripper's `0..100` normalized range, `drive_mode: 1` maps commands as
`100 - value`, reversing open/close direction.

## Apply Calibration Edits

After editing the calibration JSON file, run calibration with the same
`--robot.id` and press ENTER when prompted to use the provided calibration file.
This writes the JSON values to the Feetech motors.

```bash
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port=<follower-port> \
  --robot.id=<follower-id>
```
