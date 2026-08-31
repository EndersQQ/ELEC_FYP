# FSR and IMU Classification

This pipeline records manual labels beside the existing schema-1 FSR/IMU stream, creates fixed-time feature windows, trains a small scikit-learn classifier, and runs live inference with a transparent vibration/grasp-state detector.

## Current Scope

- Nine calibrated FSR percentages are sampled at approximately 50 Hz.
- The MPU6050 sample carried by each `FRAME` is also approximately 50 Hz.
- FSR classification is ready for data collection and training.
- IMU vibration features are a coarse baseline at 50 Hz. Reliable higher-frequency vibration work needs a later firmware sampling/protocol upgrade.
- Detection is advisory only. It does not command the gripper.

## Set Up Python

```bash
cd so-101
./software/scripts/setup_camera_ml_env.sh
source software/.venv/bin/activate
```

The ML environment contains pyserial, NumPy, scikit-learn, and joblib. A camera is not required for sensor-only training.

## Record Labeled Episodes

Stop the web UI or ROS bridge first because only one process can own the serial port.

```bash
python software/tools/record_labeled_sensor_episode.py --port /dev/ttyUSB0
```

The default keys are:

```text
1 no_contact
2 touch
3 stable_grasp
4 slip
5 impact
6 robot_motion
space pause labeling
q stop
```

Supply a different label vocabulary when needed:

```bash
python software/tools/record_labeled_sensor_episode.py \
  --labels no_contact,cube,bottle,soft_object
```

Each run creates:

```text
data/raw/episode_YYYYMMDD_HHMMSS/
  metadata.json
  sensor.jsonl
  labels.jsonl
  summary.json
```

Record multiple independent episodes for every class. Include ordinary robot motion so vibration from the servos is not learned as object slip. Label transitions are automatically excluded because a training window must fit completely inside one label interval.

## Inspect the Windowed Dataset

```bash
python software/tools/build_sensor_dataset.py data/raw
```

The default 500 ms window and 100 ms hop can be changed with `--window-ms` and `--hop-ms`. Generated features include per-zone pressure statistics, total pressure, active zones, centroid movement, acceleration/gyro variation, jerk, and coarse frequency-band energy.

## Train

The default is a random-forest FSR classifier:

```bash
python software/tools/train_fsr_imu_classifier.py data/raw --modality fsr
```

Other baselines:

```bash
python software/tools/train_fsr_imu_classifier.py data/raw --modality imu
python software/tools/train_fsr_imu_classifier.py data/raw --modality fused
python software/tools/train_fsr_imu_classifier.py data/raw --modality fsr --model logistic
```

At least two episodes are required. Training and validation are split by complete episode, not overlapping windows. The trainer saves both a joblib artifact and a readable metrics JSON file under `data/processed/`.

## Run Live

Rule-based pressure/vibration state only:

```bash
python software/tools/run_sensor_classifier.py --port /dev/ttyUSB0
```

With a trained model:

```bash
python software/tools/run_sensor_classifier.py \
  --port /dev/ttyUSB0 \
  --model data/processed/fsr_classifier.joblib
```

Use `--json` for machine-readable output. Low-confidence predictions become `unknown`. The separate fusion state reports `no_contact`, `touch`, `stable_grasp`, `possible_slip`, `slip`, `impact`, or `robot_motion` after debounce.

## Google Colab

Hardware recording stays local. Upload or synchronize the repository and ignored `data/raw/` episode folders to Google Drive, open `software/notebooks/fsr_imu_baseline_colab.ipynb`, set `PROJECT_DIR`, and run the cells. Download the resulting `.joblib` and `.metrics.json` files back to `data/processed/` for local inference.

## Data-Collection Checklist

- Leave all FSR pads released during idle calibration.
- Press every FSR zone individually before recording a dataset.
- Record multiple objects, grip forces, poses, and motion speeds.
- Include negative examples: no contact, arm movement, and motor movement.
- Keep raw episodes unchanged and rebuild derived features when feature logic changes.
- Judge performance from per-class recall and the confusion matrix, not training accuracy.
