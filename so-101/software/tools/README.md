# Tools

Command-line tools live here.

- `record_sensor_log.py` records only ESP32 FSR/IMU serial data.
- `check_camera.py` lists cameras and captures/preview-tests one camera.
- `record_multimodal_episode.py` records camera frames plus optional ESP32 serial data.
- `train_contact_baseline.py` trains the starter contact/no-contact model from recorded episodes.

Run from `so-101/` after activating the camera/ML environment when needed:

```bash
source software/.venv/bin/activate
python software/tools/check_camera.py --list
```
