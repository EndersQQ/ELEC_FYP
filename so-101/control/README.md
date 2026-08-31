# SO-101 Control

SO-101 leader/follower control uses the Seeed-tested LeRobot checkout and
Miniforge environment from the Seeed Studio guide:

- source checkout: `~/lerobot`
- Conda environment: `lerobot`

Activate it from any terminal:

```bash
conda activate lerobot
```

If `conda` is not available in a newly opened shell, load Miniforge first:

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate lerobot
```

In VS Code, select `~/miniforge3/envs/lerobot/bin/python` with
**Python: Select Interpreter**. The LeRobot package is installed in editable
mode from `~/lerobot` with Feetech support.

The current calibrated device IDs are `main_follower` and `main_leader`. These
are local, user-chosen IDs—not LeRobot defaults. LeRobot uses each ID to name
and find its calibration file, so reuse the same IDs for calibration and
teleoperation. Use `lerobot-find-port` to identify the controller ports first.

Planned work:

- connect to SO-101 joint state and action APIs
- log robot actions into recorded episodes
- add a basic grasp state machine
- later convert successful demonstrations into LeRobot datasets

Target episode file:

```text
data/raw/episode_YYYYMMDD_HHMMSS/robot_actions.jsonl
```
