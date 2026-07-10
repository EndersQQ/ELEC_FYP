# Contributing

This repository is for an ELEC final-year project, so keep changes traceable and easy to review.

## Branch Workflow

- `main` is the stable branch.
- Use `feature/<topic>` for implementation work.
- Use `docs/<topic>` for documentation-only work.
- Use `experiment/<topic>` for temporary research or testing branches.

Examples:

```text
feature/imu-driver
feature/camera-capture
docs/update-summary-log
experiment/slip-detection-v1
```

## Before Committing

For FSR9 firmware/tooling changes:

```bash
cd fsr9
/home/enders/.platformio/penv/bin/pio run
python3 -m unittest discover -s test -p 'test_*.py'
```

## Commit Messages

Use concise messages that describe the real change:

```text
Add FSR9 serial frame parser
Save FSR calibration to flash
Document next session handoff
```

Avoid vague messages such as `update`, `fix`, or `changes`.

## Documentation

Update these files regularly:

- `fsr9/docs/summary-log.md`
- `fsr9/docs/next-session-handoff.md`

Use lower-case filenames with hyphens for new documentation.
