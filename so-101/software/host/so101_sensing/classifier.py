from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .features import FEATURE_VERSION, extract_window_features


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    probabilities: dict[str, float]


class SensorClassifier:
    def __init__(self, artifact: Mapping[str, Any], confidence_threshold: float = 0.6):
        if int(artifact.get("feature_version", -1)) != FEATURE_VERSION:
            raise ValueError(
                f"Model feature version {artifact.get('feature_version')} does not match runtime version {FEATURE_VERSION}"
            )
        feature_names = artifact.get("feature_names")
        if not isinstance(feature_names, list) or not feature_names:
            raise ValueError("Model artifact has no feature_names")
        if "model" not in artifact:
            raise ValueError("Model artifact has no model")

        self.artifact = dict(artifact)
        self.model = artifact["model"]
        self.feature_names = [str(name) for name in feature_names]
        self.class_names = [str(name) for name in artifact.get("class_names", [])]
        self.modality = str(artifact.get("modality", "fused"))
        self.window_ms = int(artifact.get("window_ms", 500))
        self.hop_ms = int(artifact.get("hop_ms", 100))
        self.confidence_threshold = confidence_threshold

    @classmethod
    def load(cls, path: Path, confidence_threshold: float = 0.6) -> "SensorClassifier":
        try:
            import joblib
        except ImportError as error:
            raise RuntimeError("joblib is required to load a sensor classifier") from error
        return cls(joblib.load(path), confidence_threshold)

    def predict_features(self, features: Mapping[str, float]) -> Prediction:
        missing = [name for name in self.feature_names if name not in features]
        if missing:
            raise ValueError(f"Feature vector is missing {len(missing)} values, including {missing[:3]}")
        row = [[float(features[name]) for name in self.feature_names]]
        probabilities_array = self.model.predict_proba(row)[0]
        model_classes = [str(value) for value in self.model.classes_]
        probabilities = {
            label: float(probability) for label, probability in zip(model_classes, probabilities_array)
        }
        best_label, confidence = max(probabilities.items(), key=lambda item: item[1])
        label = best_label if confidence >= self.confidence_threshold else "unknown"
        return Prediction(label, confidence, probabilities)

    def predict_window(self, frames: Sequence[Mapping[str, Any]]) -> tuple[Prediction, dict[str, float]]:
        features = extract_window_features(frames)
        return self.predict_features(features), features
