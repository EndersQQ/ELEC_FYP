# ROS 2 Workspace

ROS 2 bridge code lives here.

Current package:

```text
src/so101_sensing_bridge
```

It reads ESP32 serial `FRAME` messages and publishes sensor/contact information into ROS 2. This is the path toward synchronized robot state, camera, tactile, and action logging.

Build when ROS 2 and `colcon` are installed:

```bash
cd ros2_ws
colcon build --symlink-install
```
