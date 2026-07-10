# GitHub Workflow

Use this workflow to keep `EndersQQ/ELEC_FYP` readable and professional.

## Branches

- `main`  
  Stable branch. Keep this buildable and readable. Use it for completed work only.

- `feature/<topic>`  
  New development work, for example:
  - `feature/imu-driver`
  - `feature/camera-capture`
  - `feature/ros2-recording`

- `docs/<topic>`  
  Documentation-only updates, for example:
  - `docs/update-handoff`
  - `docs/experiment-notes`

- `experiment/<topic>`  
  Temporary research branches. These can be messy while testing, but should be cleaned before merging.

## Recommended Routine

1. Start from latest `main`.
2. Create a topic branch.
3. Make focused commits.
4. Run firmware build and parser tests.
5. Merge into `main` when the work is usable.

Example:

```bash
git checkout main
git pull
git checkout -b feature/imu-driver
```

After edits:

```bash
/home/enders/.platformio/penv/bin/pio run
python3 -m unittest discover -s test -p 'test_*.py'
git add fsr9
git commit -m "Add MPU6050 IMU driver"
git push -u origin feature/imu-driver
```

## Commit Message Style

Use short, direct messages:

```text
Add structured FSR frame parser
Save FSR calibration to flash
Document next session handoff
```

Avoid vague messages:

```text
Update
Fix
Stuff
```

## Repository Layout

Keep hardware/software areas separated:

```text
fsr9/
  src/
  web-ui/
  host/
  tools/
  ros2_ws/
  docs/
```

Future additions should follow the same pattern:

```text
camera/
robot-control/
experiments/
```

## Before Pushing

Run:

```bash
/home/enders/.platformio/penv/bin/pio run
python3 -m unittest discover -s test -p 'test_*.py'
```

Do not commit generated files:

- `.pio/`
- `__pycache__/`
- `.ui-bridge.log`
- `.ui-bridge.pid`
- raw experiment data
