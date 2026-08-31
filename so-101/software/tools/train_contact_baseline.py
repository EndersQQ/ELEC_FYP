#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.camera import import_cv2  # noqa: E402


def import_ml_dependencies():
    try:
        import joblib
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split
    except ImportError as error:
        raise SystemExit(
            "numpy, scikit-learn, and joblib are required. "
            "Run: ./scripts/setup_camera_ml_env.sh"
        ) from error
    return joblib, np, LogisticRegression, classification_report, train_test_split


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def nearest_sensor_frame(sensor_frames: list[dict[str, Any]], host_time_ns: int, max_delta_ns: int) -> dict[str, Any] | None:
    if not sensor_frames:
        return None
    nearest = min(sensor_frames, key=lambda frame: abs(int(frame["host_time_ns"]) - host_time_ns))
    if abs(int(nearest["host_time_ns"]) - host_time_ns) > max_delta_ns:
        return None
    return nearest


def load_examples(args: argparse.Namespace, np):
    cv2 = import_cv2()

    features = []
    labels = []
    examples = []
    max_delta_ns = int(args.max_delta_ms * 1_000_000)

    for episode in sorted(args.episodes):
        sensor_frames = [
            frame for frame in read_jsonl(episode / "sensor.jsonl") if "features" in frame and "host_time_ns" in frame
        ]
        camera_frames = [
            frame
            for frame in read_jsonl(episode / "camera_frames.jsonl")
            if frame.get("camera") == args.camera and "host_time_ns" in frame
        ]

        for camera_frame in camera_frames:
            sensor_frame = nearest_sensor_frame(sensor_frames, int(camera_frame["host_time_ns"]), max_delta_ns)
            if sensor_frame is None:
                continue

            image_path = episode / camera_frame["path"]
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue

            image = cv2.resize(image, (args.width, args.height), interpolation=cv2.INTER_AREA)
            features.append((image.astype("float32") / 255.0).reshape(-1))
            total_pressure = int(sensor_frame["features"]["total_pressure"])
            labels.append(1 if total_pressure >= args.contact_threshold else 0)
            examples.append({"episode": str(episode), "image": camera_frame["path"], "total_pressure": total_pressure})

    if not features:
        raise SystemExit("No paired camera/sensor examples found. Record with --serial-port first.")

    return np.asarray(features), np.asarray(labels), examples


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a tiny contact/no-contact baseline from recorded SO-101 episodes.")
    parser.add_argument("episodes", nargs="*", type=Path, default=[SO101_DIR / "data" / "raw"])
    parser.add_argument("--camera", default="setup")
    parser.add_argument("--contact-threshold", type=int, default=5)
    parser.add_argument("--max-delta-ms", type=float, default=100.0)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=48)
    parser.add_argument("--output", type=Path, default=SO101_DIR / "data" / "processed" / "contact_baseline.joblib")
    args = parser.parse_args()

    episode_dirs = []
    for path in args.episodes:
        if (path / "metadata.json").exists():
            episode_dirs.append(path)
        elif path.exists():
            episode_dirs.extend(sorted(child for child in path.iterdir() if (child / "metadata.json").exists()))
    args.episodes = episode_dirs

    if not args.episodes:
        raise SystemExit("No episode directories found.")

    joblib, np, LogisticRegression, classification_report, train_test_split = import_ml_dependencies()
    x, y, examples = load_examples(args, np)

    if len(set(y.tolist())) < 2:
        raise SystemExit("Training needs both contact and no-contact examples. Record a more varied episode.")
    _, class_counts = np.unique(y, return_counts=True)
    if int(class_counts.min()) < 2:
        raise SystemExit("Training needs at least two examples per class for a validation split.")

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=7, stratify=y)
    model = LogisticRegression(max_iter=500, class_weight="balanced")
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "camera": args.camera,
            "image_size": [args.width, args.height],
            "contact_threshold": args.contact_threshold,
            "examples": examples[:20],
        },
        args.output,
    )

    print(classification_report(y_test, predictions, target_names=["no_contact", "contact"]))
    print(f"Saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
