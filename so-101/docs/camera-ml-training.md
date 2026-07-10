# Camera ML Training

This guide explains how to enable the initial camera training process and where the data is stored.

## What Training Means Right Now

The current ML tool is a small baseline, not the final SO-101 robot policy.

It trains a simple **contact/no-contact classifier** from:

- camera frames from the setup Logitech/UVC camera, and
- nearest FSR pressure frames from the ESP32 serial stream.

The label is generated automatically:

```text
total FSR pressure >= contact threshold  -> contact
total FSR pressure < contact threshold   -> no contact
```

This proves that camera frames and tactile frames can be recorded, aligned, and used for training before moving to LeRobot demonstrations.

## One-Time Setup

Run this from the SO-101 project folder:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
./software/scripts/setup_camera_ml_env.sh
source software/.venv/bin/activate
```

This installs OpenCV, NumPy, scikit-learn, joblib, and pyserial into:

```text
so-101/software/.venv/
```

## Check the Camera

List connected cameras:

```bash
python software/tools/check_camera.py --list
```

Capture a test image:

```bash
python software/tools/check_camera.py --device /dev/video0 --name setup --capture
```

Test images are stored in:

```text
so-101/data/raw/camera_checks/
```

## Record Training Data

For camera-only setup testing:

```bash
python software/tools/record_multimodal_episode.py \
  --camera setup=/dev/video0 \
  --duration 10
```

For usable training data, include the ESP32 serial stream:

```bash
python software/tools/record_multimodal_episode.py \
  --camera setup=/dev/video0 \
  --serial-port /dev/ttyUSB0 \
  --duration 30
```

Each run creates a new folder:

```text
so-101/data/raw/episode_YYYYMMDD_HHMMSS/
```

Inside each episode:

```text
metadata.json              Camera and serial configuration
summary.json               How many frames were recorded
sensor.jsonl               ESP32 FSR/IMU frames with host timestamps
camera_frames.jsonl        Camera frame index with host timestamps
cameras/setup/*.jpg        Captured setup camera frames
```

## Train the Baseline Model

After recording at least one episode with both **no contact** and **contact** examples:

```bash
python software/tools/train_contact_baseline.py data/raw --camera setup
```

The trained model is saved to:

```text
so-101/data/processed/contact_baseline.joblib
```

You can tune the pressure threshold:

```bash
python software/tools/train_contact_baseline.py data/raw --camera setup --contact-threshold 10
```

## Later With Two IMX335 Cameras

The final two-camera setup uses the same recorder. Use stable camera device symlinks from `/dev/v4l/by-id/` when possible:

```bash
python software/tools/record_multimodal_episode.py \
  --camera gripper=/dev/v4l/by-id/<gripper-camera-id> \
  --camera table=/dev/v4l/by-id/<table-camera-id> \
  --serial-port /dev/ttyUSB0 \
  --duration 30
```

That creates:

```text
so-101/data/raw/episode_YYYYMMDD_HHMMSS/
  cameras/gripper/*.jpg
  cameras/table/*.jpg
```

The current baseline trainer uses one camera at a time:

```bash
python software/tools/train_contact_baseline.py data/raw --camera gripper
python software/tools/train_contact_baseline.py data/raw --camera table
```

The next larger ML step is to add SO-101 joint/action logs and convert successful synchronized episodes into a LeRobot dataset.
