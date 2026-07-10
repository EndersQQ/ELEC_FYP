from __future__ import annotations

import json
import threading
import time

import serial

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String

from so101_sensing import FsrImuFrame, parse_line


class FsrImuBridge(Node):
    def __init__(self) -> None:
        super().__init__("fsr_imu_bridge")
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baud", 115200)
        self.declare_parameter("frame_topic", "/so101/gripper/fsr_imu/frame_json")
        self.declare_parameter("features_topic", "/so101/gripper/contact_features")
        self.declare_parameter("status_topic", "/so101/gripper/fsr_imu/status")

        self.port = self.get_parameter("port").get_parameter_value().string_value
        self.baud = self.get_parameter("baud").get_parameter_value().integer_value

        self.frame_pub = self.create_publisher(
            String, self.get_parameter("frame_topic").get_parameter_value().string_value, 10
        )
        self.features_pub = self.create_publisher(
            Float32MultiArray, self.get_parameter("features_topic").get_parameter_value().string_value, 10
        )
        self.status_pub = self.create_publisher(
            String, self.get_parameter("status_topic").get_parameter_value().string_value, 10
        )

        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._read_serial, daemon=True)
        self._worker.start()
        self.get_logger().info(f"Reading FSR/IMU frames from {self.port} at {self.baud} baud")

    def destroy_node(self) -> bool:
        self._stop_event.set()
        self._worker.join(timeout=2.0)
        return super().destroy_node()

    def _read_serial(self) -> None:
        while not self._stop_event.is_set():
            try:
                with serial.Serial(self.port, self.baud, timeout=1) as device:
                    self._publish_status({"state": "serial_connected", "port": self.port, "baud": self.baud})
                    while not self._stop_event.is_set():
                        line = device.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            self._handle_line(line)
            except serial.SerialException as error:
                self._publish_status({"state": "serial_error", "error": str(error)})
                time.sleep(1.0)

    def _handle_line(self, line: str) -> None:
        try:
            parsed = parse_line(line)
        except (TypeError, ValueError) as error:
            self._publish_status({"state": "parse_error", "error": str(error), "line": line})
            return

        if isinstance(parsed, FsrImuFrame):
            self._publish_frame(parsed)
            self._publish_features(parsed)
        elif isinstance(parsed, dict):
            self._publish_status(parsed)

    def _publish_frame(self, frame: FsrImuFrame) -> None:
        msg = String()
        msg.data = json.dumps({"host_time_ns": time.time_ns(), **frame.to_dict()})
        self.frame_pub.publish(msg)

    def _publish_features(self, frame: FsrImuFrame) -> None:
        centroid = frame.contact_centroid
        strongest = frame.strongest_sensor
        msg = Float32MultiArray()
        msg.data = [
            float("nan") if centroid is None else float(centroid[0]),
            float("nan") if centroid is None else float(centroid[1]),
            float(frame.total_pressure),
            float(frame.active_count),
            float("nan") if strongest is None else float(strongest.sensor),
            float("nan") if strongest is None else float(strongest.percent),
            1.0 if frame.imu.available else 0.0,
            float(frame.imu.temp_c),
        ]
        self.features_pub.publish(msg)

    def _publish_status(self, payload: dict) -> None:
        msg = String()
        msg.data = json.dumps(payload)
        self.status_pub.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FsrImuBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
