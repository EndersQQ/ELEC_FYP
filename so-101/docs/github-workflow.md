# GitHub Workflow

Use this workflow to keep `EndersQQ/ELEC_FYP` readable and professional.

## Branch Policy

GitHub should keep one stable branch:

```text
main
```

Temporary feature branches are fine locally while developing, but clean them up after merging so the GitHub branch list does not become confusing.

## Repository Layout

The GitHub root should show:

```text
so-101/
README.md
CONTRIBUTING.md
```

The SO-101 project is organized by purpose:

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

## Before Pushing

Firmware build:

```bash
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Python tests:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

## Commit Message Style

Use short, direct messages:

```text
Reorganize SO-101 repository layout
Add structured FSR frame parser
Document camera training workflow
```

Avoid vague messages:

```text
Update
Fix
Stuff
```

## Do Not Commit

- `.pio/`
- `__pycache__/`
- `.venv/`
- `.ui-bridge.log`
- `.ui-bridge.pid`
- raw experiment data
- trained model binaries unless intentionally versioned
