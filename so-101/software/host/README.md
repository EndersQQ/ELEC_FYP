# Host Python Package

Reusable Python code lives here. These files are imported by tools, tests, and later ROS/ML scripts.

- `so101_sensing/parser.py` parses ESP32 serial lines.
- `so101_sensing/camera.py` handles host-connected cameras.

Do not put one-off command-line scripts here. Put runnable scripts in `tools/`.
