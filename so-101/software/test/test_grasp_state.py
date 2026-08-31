import sys
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.grasp_state import GraspStateMachine, VibrationDetector  # noqa: E402


def base_features(**updates) -> dict[str, float]:
    features = {
        "fsr_total_mean": 0.0,
        "fsr_total_delta": 0.0,
        "fsr_centroid_motion_mean": 0.0,
        "imu_accel_highpass_rms": 0.0,
        "imu_gyro_highpass_rms": 0.0,
        "imu_accel_peak_to_peak": 0.0,
    }
    for number in range(1, 10):
        features[f"fsr_s{number}_max"] = 0.0
    features.update(updates)
    return features


class GraspStateTest(unittest.TestCase):
    def test_debounces_stable_grasp(self):
        machine = GraspStateMachine(transition_windows=3)
        features = base_features(fsr_total_mean=40.0, fsr_s5_max=40.0)

        self.assertEqual(machine.update(features).state, "no_contact")
        self.assertEqual(machine.update(features).state, "no_contact")
        self.assertEqual(machine.update(features).state, "stable_grasp")

    def test_contact_vibration_and_pressure_change_becomes_slip(self):
        detector = VibrationDetector(enter_windows=1)
        machine = GraspStateMachine(transition_windows=1, vibration_detector=detector)
        features = base_features(
            fsr_total_mean=40.0,
            fsr_total_delta=-12.0,
            fsr_s5_max=40.0,
            imu_accel_highpass_rms=0.7,
        )

        result = machine.update(features)

        self.assertTrue(result.vibration.active)
        self.assertEqual(result.state, "slip")

    def test_vibration_without_contact_is_robot_motion(self):
        detector = VibrationDetector(enter_windows=1)
        machine = GraspStateMachine(transition_windows=1, vibration_detector=detector)

        result = machine.update(base_features(imu_gyro_highpass_rms=16.0))

        self.assertEqual(result.state, "robot_motion")


if __name__ == "__main__":
    unittest.main()
