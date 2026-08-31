# Host Python Package

Reusable Python code lives here. These files are imported by tools, tests, and later ROS/ML scripts.

- `so101_sensing/parser.py` parses ESP32 serial lines.
- `so101_sensing/camera.py` handles host-connected cameras.
- `so101_sensing/features.py` extracts fixed-window pressure and vibration features.
- `so101_sensing/dataset.py` aligns labels and sensor windows.
- `so101_sensing/classifier.py` validates model artifacts and runs predictions.
- `so101_sensing/grasp_state.py` provides vibration detection and debounced state fusion.

Do not put one-off command-line scripts here. Put runnable scripts in `tools/`.
