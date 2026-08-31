#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.dataset import build_labeled_examples, class_counts, discover_episode_dirs  # noqa: E402
from so101_sensing.features import FEATURE_VERSION  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build windowed FSR/IMU features from labeled episodes.")
    parser.add_argument("episodes", nargs="*", type=Path, default=[SO101_DIR / "data" / "raw"])
    parser.add_argument("--window-ms", type=int, default=500)
    parser.add_argument("--hop-ms", type=int, default=100)
    parser.add_argument("--minimum-frames", type=int, default=4)
    parser.add_argument(
        "--output", type=Path, default=SO101_DIR / "data" / "processed" / "fsr_imu_features.jsonl"
    )
    args = parser.parse_args()

    episodes = discover_episode_dirs(args.episodes)
    if not episodes:
        raise SystemExit("No labeled episode directories found.")
    examples = build_labeled_examples(episodes, args.window_ms, args.hop_ms, args.minimum_frames)
    if not examples:
        raise SystemExit("No fully labeled feature windows were produced.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for example in examples:
            payload = {"feature_version": FEATURE_VERSION, **example.to_dict()}
            handle.write(json.dumps(payload, separators=(",", ":")) + "\n")

    print(json.dumps({"episodes": len(episodes), "examples": len(examples), "classes": class_counts(examples)}, indent=2))
    print(f"Saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
