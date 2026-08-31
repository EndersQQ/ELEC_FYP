# Tools

Command-line tools live here.

- `record_sensor_log.py` records only ESP32 FSR/IMU serial data.
- `record_labeled_sensor_episode.py` records sensor frames with interactive label intervals.
- `build_sensor_dataset.py` converts labeled episodes into inspectable fixed-window features.
- `train_fsr_imu_classifier.py` trains FSR, IMU, or fused scikit-learn classifiers.
- `run_sensor_classifier.py` runs live model inference and the vibration/grasp-state detector.
- `check_camera.py` lists cameras and captures/preview-tests one camera.
- `record_multimodal_episode.py` records camera frames plus optional ESP32 serial data.
- `train_contact_baseline.py` trains the starter contact/no-contact model from recorded episodes.
- `check_so101_motors.py` checks that both configured Feetech buses can see servo IDs 1–6.

The motor check requires the separate LeRobot environment; the other basic serial tools use `requirements.txt`.

Run from `so-101/` after activating the camera/ML environment when needed:

```bash
source software/.venv/bin/activate
python software/tools/check_camera.py --list
```

The sensor classifier workflow is documented in `docs/sensor-ml-training.md`.
