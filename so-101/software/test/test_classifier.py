import sys
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.classifier import SensorClassifier  # noqa: E402
from so101_sensing.features import FEATURE_VERSION  # noqa: E402


class FakeModel:
    classes_ = ["no_contact", "stable_grasp"]

    def predict_proba(self, rows):
        return [[0.1, 0.9] for _ in rows]


class ClassifierTest(unittest.TestCase):
    def test_predicts_with_artifact_feature_order(self):
        classifier = SensorClassifier(
            {
                "model": FakeModel(),
                "feature_version": FEATURE_VERSION,
                "feature_names": ["fsr_total_mean", "fsr_s1_max"],
                "class_names": ["no_contact", "stable_grasp"],
                "modality": "fsr",
            }
        )

        prediction = classifier.predict_features({"fsr_s1_max": 30.0, "fsr_total_mean": 40.0})

        self.assertEqual(prediction.label, "stable_grasp")
        self.assertAlmostEqual(prediction.confidence, 0.9)

    def test_rejects_incompatible_feature_version(self):
        with self.assertRaises(ValueError):
            SensorClassifier(
                {"model": FakeModel(), "feature_version": FEATURE_VERSION + 1, "feature_names": ["x"]}
            )


if __name__ == "__main__":
    unittest.main()
