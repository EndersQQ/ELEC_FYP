#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.dataset import build_labeled_examples, class_counts, discover_episode_dirs  # noqa: E402
from so101_sensing.features import FEATURE_VERSION, select_feature_names  # noqa: E402


def import_dependencies():
    try:
        import joblib
        import numpy as np
        from sklearn.base import clone
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report, confusion_matrix
        from sklearn.model_selection import GroupShuffleSplit
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as error:
        raise SystemExit(
            "NumPy, scikit-learn, and joblib are required. Run ./software/scripts/setup_camera_ml_env.sh"
        ) from error
    return {
        "joblib": joblib,
        "np": np,
        "clone": clone,
        "RandomForestClassifier": RandomForestClassifier,
        "LogisticRegression": LogisticRegression,
        "classification_report": classification_report,
        "confusion_matrix": confusion_matrix,
        "GroupShuffleSplit": GroupShuffleSplit,
        "Pipeline": Pipeline,
        "StandardScaler": StandardScaler,
    }


def choose_group_split(labels, groups, splitter_class, test_size: float):
    all_classes = set(labels)
    splitter = splitter_class(n_splits=40, test_size=test_size, random_state=7)
    placeholder = [[0.0] for _ in labels]
    for train_indices, test_indices in splitter.split(placeholder, labels, groups):
        if set(labels[index] for index in train_indices) == all_classes and set(
            labels[index] for index in test_indices
        ) == all_classes:
            return train_indices, test_indices
    raise SystemExit(
        "Could not create an episode-level validation split containing every class. "
        "Record each class in more independent episodes."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Train an FSR, IMU, or fused classifier from labeled episodes.")
    parser.add_argument("episodes", nargs="*", type=Path, default=[SO101_DIR / "data" / "raw"])
    parser.add_argument("--modality", choices=["fsr", "imu", "fused"], default="fsr")
    parser.add_argument("--model", choices=["random-forest", "logistic"], default="random-forest")
    parser.add_argument("--window-ms", type=int, default=500)
    parser.add_argument("--hop-ms", type=int, default=100)
    parser.add_argument("--minimum-frames", type=int, default=4)
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    episodes = discover_episode_dirs(args.episodes)
    if len(episodes) < 2:
        raise SystemExit("Training needs at least two labeled episodes for an episode-level split.")
    examples = build_labeled_examples(episodes, args.window_ms, args.hop_ms, args.minimum_frames)
    counts = class_counts(examples)
    if len(counts) < 2:
        raise SystemExit("Training needs at least two label classes.")

    feature_names = select_feature_names(examples[0].features, args.modality)
    dependencies = import_dependencies()
    np = dependencies["np"]
    x = np.asarray([[example.features[name] for name in feature_names] for example in examples], dtype="float64")
    y = np.asarray([example.label for example in examples])
    groups = np.asarray([example.episode for example in examples])
    train_indices, test_indices = choose_group_split(y, groups, dependencies["GroupShuffleSplit"], args.test_size)

    if args.model == "logistic":
        estimator = dependencies["Pipeline"](
            [
                ("scale", dependencies["StandardScaler"]()),
                (
                    "model",
                    dependencies["LogisticRegression"](max_iter=1000, class_weight="balanced", random_state=7),
                ),
            ]
        )
    else:
        estimator = dependencies["RandomForestClassifier"](
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=7,
            n_jobs=-1,
        )

    validation_model = dependencies["clone"](estimator)
    validation_model.fit(x[train_indices], y[train_indices])
    predictions = validation_model.predict(x[test_indices])
    class_names = sorted(counts)
    report = dependencies["classification_report"](
        y[test_indices], predictions, labels=class_names, output_dict=True, zero_division=0
    )
    matrix = dependencies["confusion_matrix"](y[test_indices], predictions, labels=class_names).tolist()

    final_model = dependencies["clone"](estimator)
    final_model.fit(x, y)
    output = args.output or SO101_DIR / "data" / "processed" / f"{args.modality}_classifier.joblib"
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": final_model,
        "feature_version": FEATURE_VERSION,
        "frame_schema": 1,
        "feature_names": feature_names,
        "class_names": class_names,
        "modality": args.modality,
        "window_ms": args.window_ms,
        "hop_ms": args.hop_ms,
        "model_type": args.model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_episodes": sorted(set(groups.tolist())),
        "validation_episodes": sorted(set(groups[test_indices].tolist())),
        "class_counts": counts,
        "validation": {"classification_report": report, "confusion_matrix": matrix},
    }
    dependencies["joblib"].dump(artifact, output)
    metrics_path = output.with_suffix(".metrics.json")
    metrics_path.write_text(
        json.dumps({key: value for key, value in artifact.items() if key != "model" and key != "feature_names"}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    print(dependencies["classification_report"](y[test_indices], predictions, labels=class_names, zero_division=0))
    print("Confusion matrix labels:", class_names)
    print(np.asarray(matrix))
    print(f"Saved {output}")
    print(f"Saved {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
