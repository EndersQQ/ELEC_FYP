import json
import sys
import tempfile
import unittest
from pathlib import Path


SOFTWARE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.dataset import build_labeled_examples, discover_episode_dirs  # noqa: E402
from test_features import make_frame  # noqa: E402


class DatasetTest(unittest.TestCase):
    def test_builds_only_fully_labeled_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "episode_one"
            episode.mkdir()
            frames = [make_frame(index, pressure=20.0) for index in range(35)]
            (episode / "sensor.jsonl").write_text(
                "".join(json.dumps(frame) + "\n" for frame in frames), encoding="utf-8"
            )
            (episode / "labels.jsonl").write_text(
                json.dumps(
                    {
                        "label": "stable_grasp",
                        "start_host_time_ns": 0,
                        "end_host_time_ns": 1_000_000_000,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            episodes = discover_episode_dirs([Path(directory)])
            examples = build_labeled_examples(episodes, window_ms=500, hop_ms=100)

            self.assertEqual(episodes, [episode.resolve()])
            self.assertEqual(len(examples), 2)
            self.assertEqual(examples[0].label, "stable_grasp")
            self.assertEqual(examples[0].features["fsr_total_mean"], 20.0)


if __name__ == "__main__":
    unittest.main()
