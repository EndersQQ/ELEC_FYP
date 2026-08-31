# SO-101 Gripper Sensing Documentation

This folder keeps project notes that should be updated often.

## Main Documents

- `PROJECT_SUMMARY.md`  
  High-level project overview and current folder naming note.

- `repository-map.md`  
  What each top-level folder and important file is for.

- `codebase-guide.md`
  What every executable source file does and how data moves through the system.

- `camera-ml-training.md`  
  How to record camera data, train the starter model, and find saved outputs.

- `sensor-ml-training.md`
  How to label FSR/IMU episodes, train sensor classifiers, and run live inference.

- `software-architecture.md`  
  Current software architecture, commands, and integration direction.

- `github-workflow.md`  
  Branch and commit workflow for keeping the GitHub repository professional.

## Naming Rule

Use lower-case filenames with hyphens for normal docs, for example:

```text
camera-calibration-notes.md
imu-integration-log.md
experiment-2026-07-10.md
```

For recurring documents, prefer stable names instead of date-only names. Put dates inside the document as headings.

`PROJECT_SUMMARY.md` is the one intentional uppercase entrypoint because it is meant to be easy to spot in the IDE.
