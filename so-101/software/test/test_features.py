import math
import sys
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.features import extract_window_features, iter_feature_windows  # noqa: E402


def make_frame(index: int, pressure: float = 0.0, vibration: float = 0.0) -> dict:
    return {
        "host_time_ns": index * 20_000_000,
        "device_ms": index * 20,
        "sensors": [
            {"sensor": number, "raw": 1000 + number, "percent": pressure if number == 5 else 0.0}
            for number in range(1, 10)
        ],
        "imu": {
            "available": True,
            "accel_x": vibration if index % 2 == 0 else -vibration,
            "accel_y": 0.0,
            "accel_z": 9.80665,
            "gyro_x": vibration * 10.0 if index % 2 == 0 else -vibration * 10.0,
            "gyro_y": 0.0,
            "gyro_z": 0.0,
            "temp_c": 30.0,
        },
    }


class FeatureTest(unittest.TestCase):
    def test_extracts_spatial_pressure_and_vibration_features(self):
        frames = [make_frame(index, pressure=float(index), vibration=0.5) for index in range(25)]

        features = extract_window_features(frames)

        self.assertAlmostEqual(features["fsr_s5_last"], 24.0)
        self.assertAlmostEqual(features["fsr_total_delta"], 24.0)
        self.assertAlmostEqual(features["fsr_centroid_x_mean"], 0.0)
        self.assertAlmostEqual(features["fsr_centroid_y_mean"], 0.0)
        self.assertAlmostEqual(features["imu_sample_rate_hz"], 50.0)
        self.assertGreater(features["imu_accel_highpass_rms"], 0.0)
        self.assertTrue(math.isfinite(features["imu_accel_dominant_hz"]))

    def test_iterates_fixed_windows(self):
        frames = [make_frame(index) for index in range(40)]

        windows = list(iter_feature_windows(frames, window_ms=500, hop_ms=100))

        self.assertEqual(len(windows), 3)
        self.assertEqual(windows[0].start_time_ns, 0)
        self.assertEqual(windows[0].end_time_ns, 500_000_000)
        self.assertEqual(len(windows[0].frames), 25)


if __name__ == "__main__":
    unittest.main()
