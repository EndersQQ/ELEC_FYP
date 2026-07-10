# Camera Perception

This folder describes the camera side of the SO-101 sensing stack.

Current camera path:

- Temporary setup camera: Logitech or other UVC camera connected to the host computer.
- Final camera plan: two IMX335 cameras connected to the host computer.

Relevant implementation files:

- Camera helper module: `../../software/host/so101_sensing/camera.py`
- Camera check tool: `../../software/tools/check_camera.py`
- Multimodal recorder: `../../software/tools/record_multimodal_episode.py`
- Training guide: `../../docs/camera-ml-training.md`

The cameras should not be routed through the ESP32-S3.
