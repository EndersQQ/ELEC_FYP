import sys
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.camera import CameraConfig, parse_camera_spec  # noqa: E402


class CameraConfigTest(unittest.TestCase):
    def test_parse_named_camera_spec(self):
        config = parse_camera_spec("gripper=/dev/video2")

        self.assertEqual(config, CameraConfig(name="gripper", device="/dev/video2"))

    def test_parse_unnamed_camera_spec(self):
        config = parse_camera_spec("/dev/video0")

        self.assertEqual(config.name, "setup")
        self.assertEqual(config.device, "/dev/video0")

    def test_reject_empty_device(self):
        with self.assertRaises(ValueError):
            parse_camera_spec("setup=")


if __name__ == "__main__":
    unittest.main()
