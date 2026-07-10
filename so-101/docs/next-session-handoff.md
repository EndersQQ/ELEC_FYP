# Next Session Handoff

Update this file at the end of each development session. Keep it short, practical, and focused on what the next session needs to know immediately.

## Current Project Location

GitHub-connected source:

```text
/home/enders/Documents/ELEC_FYP_prepared/so-101
```

GitHub repository:

```text
https://github.com/EndersQQ/ELEC_FYP
```

The old top-level `fsr9/` folder has been replaced by the professional `so-101/` project folder.

## Current Layout

```text
so-101/
  sensors/fsr9/          ESP32-S3 FSR tactile firmware
  sensors/imu/           IMU integration area
  perception/camera/     Camera setup and future IMX335 work
  control/               SO-101 control and action logging
  software/              Python host tools, package, UI, scripts, tests
  ros2_ws/               ROS 2 bridge workspace
  docs/                  Project docs
  data/                  Local outputs; raw/processed ignored by Git
```

## Current System State

The ESP32-S3 firmware reads the 9-zone FSR array and streams structured serial `FRAME` messages. Calibration is saved in flash. The browser UI can visualize live pressure data. Python host tools can parse and record data. A ROS 2 bridge scaffold exists.

The IMU fields are already included in the serial frame, but the real IMU driver is not implemented yet because the exact IMU module is not known.

A host-side camera/ML starter stack exists for initial setup with a Logitech/UVC camera and later replacement by two IMX335 cameras. Camera capture stays on the host computer.

## Verified Commands

Firmware build:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101/sensors/fsr9
/home/enders/.platformio/penv/bin/pio run
```

Python tests:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101/software
python3 -m unittest discover -s test -p 'test_*.py'
```

Camera/ML environment setup:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
./software/scripts/setup_camera_ml_env.sh
source software/.venv/bin/activate
```

## Useful Run Commands

Upload firmware:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101/sensors/fsr9
./scripts/upload_safe.sh /dev/ttyUSB0
```

Start browser UI:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101/software
./scripts/start_ui.sh /dev/ttyUSB0
```

Open:

```text
http://127.0.0.1:8090
```

Record FSR/IMU JSONL:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
python software/tools/record_sensor_log.py --port /dev/ttyUSB0 --format jsonl
```

Check camera devices:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
source software/.venv/bin/activate
python software/tools/check_camera.py --list
python software/tools/check_camera.py --device /dev/video0 --name setup --capture
```

Record setup camera plus FSR episode:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
source software/.venv/bin/activate
python software/tools/record_multimodal_episode.py --camera setup=/dev/video0 --serial-port /dev/ttyUSB0 --duration 20
```

Train starter contact/no-contact model:

```bash
cd /home/enders/Documents/ELEC_FYP_prepared/so-101
source software/.venv/bin/activate
python software/tools/train_contact_baseline.py data/raw --camera setup
```

Future two-camera IMX335 episode:

```bash
python software/tools/record_multimodal_episode.py \
  --camera gripper=/dev/v4l/by-id/<gripper-camera-id> \
  --camera table=/dev/v4l/by-id/<table-camera-id> \
  --serial-port /dev/ttyUSB0 \
  --duration 30
```

## Next Questions To Ask User

Ask these before implementing the next hardware-specific stage:

1. What exact IMU module is being used?
2. Is the IMU connected by I2C or SPI?
3. Which ESP32-S3 pins are used for the IMU?
4. How are the two IMX335 cameras connected to the host computer?
5. What OS and computer will run the camera and ROS stack?
6. Is ROS 2 installed? If yes, which distro?
7. Is LeRobot already installed for SO-101?

## Recommended Next Implementation Step

Record one real camera plus FSR episode:

1. Activate `software/.venv`.
2. Run `python software/tools/check_camera.py --list`.
3. Capture one setup image from the Logitech/UVC camera.
4. Record one 20-30 second episode with contact and no-contact moments.
5. Confirm `camera_frames.jsonl`, `sensor.jsonl`, and images are written under `data/raw/episode_*`.
6. Train the starter baseline with `train_contact_baseline.py`.
7. Then confirm IMU model/wiring and implement the real IMU driver.

## Important Notes

- Do not route the IMX335 cameras through the ESP32-S3. They should connect to the host computer.
- The IMU chip temperature usually measures board/chip temperature, not true object temperature.
- The FSR array provides a contact-pressure map, not a full object shape. Shape estimation should combine FSR data with camera images and robot pose.
- GitHub should keep one stable branch: `main`.
