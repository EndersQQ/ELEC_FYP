from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .features import extract_window_features, iter_feature_windows


@dataclass(frozen=True)
class LabelInterval:
    label: str
    start_time_ns: int
    end_time_ns: int

    def covers(self, start_time_ns: int, end_time_ns: int) -> bool:
        return self.start_time_ns <= start_time_ns and self.end_time_ns >= end_time_ns


@dataclass(frozen=True)
class LabeledExample:
    episode: str
    label: str
    start_time_ns: int
    end_time_ns: int
    features: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode": self.episode,
            "label": self.label,
            "start_time_ns": self.start_time_ns,
            "end_time_ns": self.end_time_ns,
            "features": self.features,
        }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {path}:{line_number}: {error}") from error
    return records


def discover_episode_dirs(paths: Iterable[Path]) -> list[Path]:
    episodes: set[Path] = set()
    for path in paths:
        if (path / "sensor.jsonl").exists() and (path / "labels.jsonl").exists():
            episodes.add(path.resolve())
        elif path.exists() and path.is_dir():
            for child in path.iterdir():
                if (child / "sensor.jsonl").exists() and (child / "labels.jsonl").exists():
                    episodes.add(child.resolve())
    return sorted(episodes)


def load_label_intervals(path: Path) -> list[LabelInterval]:
    intervals = []
    for record in read_jsonl(path):
        label = str(record.get("label", "")).strip()
        start = record.get("start_host_time_ns")
        end = record.get("end_host_time_ns")
        if not label or start is None or end is None:
            continue
        if int(end) <= int(start):
            continue
        intervals.append(LabelInterval(label, int(start), int(end)))
    return sorted(intervals, key=lambda interval: interval.start_time_ns)


def build_labeled_examples(
    episodes: Iterable[Path],
    window_ms: int = 500,
    hop_ms: int = 100,
    minimum_frames: int = 4,
) -> list[LabeledExample]:
    examples = []
    for episode in episodes:
        frames = read_jsonl(episode / "sensor.jsonl")
        intervals = load_label_intervals(episode / "labels.jsonl")
        for window in iter_feature_windows(frames, window_ms, hop_ms, minimum_frames):
            interval = next(
                (candidate for candidate in intervals if candidate.covers(window.start_time_ns, window.end_time_ns)),
                None,
            )
            if interval is None:
                continue
            examples.append(
                LabeledExample(
                    episode=episode.name,
                    label=interval.label,
                    start_time_ns=window.start_time_ns,
                    end_time_ns=window.end_time_ns,
                    features=extract_window_features(window.frames),
                )
            )
    return examples


def class_counts(examples: Iterable[LabeledExample]) -> dict[str, int]:
    return dict(sorted(Counter(example.label for example in examples).items()))
