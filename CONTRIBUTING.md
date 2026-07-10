# Contributing

This repository is for an ELEC final-year project, so keep changes traceable, documented, and easy to reproduce.

## Branch Workflow

Use `main` as the single stable GitHub branch.

For short experiments, use local branches if helpful, then merge or squash back into `main` before pushing. Avoid leaving old remote branches on GitHub.

## Before Committing

Firmware changes:

```bash
cd so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Python host/tool changes:

```bash
cd so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Camera/ML tool smoke check:

```bash
cd so-101
source software/.venv/bin/activate
python software/tools/check_camera.py --list
```

## Commit Messages

Use concise messages that describe the real change:

```text
Reorganize SO-101 repository layout
Add FSR serial frame parser
Document camera training workflow
```

Avoid vague messages such as `update`, `fix`, or `changes`.

## Documentation

Update these files regularly:

- `so-101/docs/PROJECT_SUMMARY.md`
- `so-101/docs/summary-log.md`
- `so-101/docs/next-session-handoff.md`

Use lower-case filenames with hyphens for normal docs. `PROJECT_SUMMARY.md` is the intentional easy-to-find entrypoint.
