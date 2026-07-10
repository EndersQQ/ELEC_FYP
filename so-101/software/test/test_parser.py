import sys
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing import FsrImuFrame, parse_line  # noqa: E402


class ParserTest(unittest.TestCase):
    def test_parse_frame_and_features(self):
        line = (
            "FRAME,1,42,12345,30,9,"
            "3000,0,2900,10,2800,20,2700,30,2600,40,2500,50,2400,60,2300,70,2200,80,"
            "1,0.1000,0.2000,9.8100,0.0100,0.0200,0.0300,31.50"
        )

        parsed = parse_line(line)

        self.assertIsInstance(parsed, FsrImuFrame)
        assert isinstance(parsed, FsrImuFrame)
        self.assertEqual(parsed.sequence, 42)
        self.assertEqual(parsed.connected_count, 9)
        self.assertEqual(parsed.total_pressure, 360)
        self.assertEqual(parsed.active_count, 8)
        self.assertEqual(parsed.strongest_sensor.sensor, 9)
        self.assertEqual(parsed.imu.available, True)
        self.assertAlmostEqual(parsed.imu.temp_c, 31.5)
        self.assertIsNotNone(parsed.contact_centroid)

    def test_parse_status(self):
        parsed = parse_line("STATUS,ready,9,30")

        self.assertEqual(parsed["type"], "status")
        self.assertEqual(parsed["state"], "ready")
        self.assertEqual(parsed["fields"], ["9", "30"])


if __name__ == "__main__":
    unittest.main()
