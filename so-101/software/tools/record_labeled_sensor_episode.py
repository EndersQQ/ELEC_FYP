#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

try:
    import serial
except ImportError as error:
    raise SystemExit("pyserial is required. Install software/requirements.txt first.") from error

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing import FsrImuFrame, parse_line  # noqa: E402


DEFAULT_LABELS = ["no_contact", "touch", "stable_grasp", "slip", "impact", "robot_motion"]


@dataclass
class ActiveLabel:
    label: str
    start_time_ns: int


class KeyboardReader:
    def __init__(self, stream: TextIO):
        self.stream = stream
        self.settings = None

    def __enter__(self) -> "KeyboardReader":
        if self.stream.isatty():
            self.settings = termios.tcgetattr(self.stream)
            tty.setcbreak(self.stream.fileno())
        return self

    def __exit__(self, *_args) -> None:
        if self.settings is not None:
            termios.tcsetattr(self.stream, termios.TCSADRAIN, self.settings)

    def read_key(self) -> str | None:
        if not self.stream.isatty():
            return None
        readable, _, _ = select.select([self.stream], [], [], 0)
        return self.stream.read(1) if readable else None


def parse_labels(value: str) -> list[str]:
    labels = [label.strip() for label in value.split(",") if label.strip()]
    if not labels:
        raise argparse.ArgumentTypeError("At least one label is required")
    if len(labels) > 9:
        raise argparse.ArgumentTypeError("Interactive recording supports at most nine labels")
    if len(set(labels)) != len(labels):
        raise argparse.ArgumentTypeError("Labels must be unique")
    return labels


def write_json_line(handle: TextIO, payload: dict) -> None:
    handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
    handle.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Record manually labeled SO-101 FSR/IMU episodes.")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--labels", type=parse_labels, default=DEFAULT_LABELS)
    parser.add_argument("--initial-label", default=None)
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds to record; 0 means until q/Ctrl+C.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    labels = args.labels if isinstance(args.labels, list) else parse_labels(args.labels)
    if args.initial_label is not None and args.initial_label not in labels:
        raise SystemExit(f"--initial-label must be one of: {', '.join(labels)}")
    if not sys.stdin.isatty() and args.initial_label is None:
        raise SystemExit("Non-interactive recording requires --initial-label.")
    if not sys.stdin.isatty() and args.duration <= 0:
        raise SystemExit("Non-interactive recording requires a positive --duration.")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    episode_dir = args.output or SO101_DIR / "data" / "raw" / f"episode_{timestamp}"
    episode_dir.mkdir(parents=True, exist_ok=False)

    metadata = {
        "created_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "recorder": "record_labeled_sensor_episode.py",
        "frame_schema": 1,
        "serial": {"port": args.port, "baud": args.baud},
        "labels": labels,
        "label_keys": {str(index + 1): label for index, label in enumerate(labels)},
        "notes": [
            "Labels are host-time intervals recorded by the same process as sensor frames.",
            "Raw sensor frames are immutable inputs; window features are generated later.",
        ],
    }
    (episode_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    frame_count = 0
    status_count = 0
    label_intervals = []
    active = ActiveLabel(args.initial_label, time.time_ns()) if args.initial_label else None
    started = time.monotonic()

    print(f"Recording -> {episode_dir}")
    for index, label in enumerate(labels, start=1):
        print(f"  {index}: {label}")
    print("  space: pause labeling")
    print("  q: stop")
    if active:
        print(f"Active label: {active.label}")

    sensor_path = episode_dir / "sensor.jsonl"
    try:
        with serial.Serial(args.port, args.baud, timeout=0.02) as device, sensor_path.open(
            "w", encoding="utf-8"
        ) as sensor_handle, KeyboardReader(sys.stdin) as keyboard:
            while args.duration <= 0 or time.monotonic() - started < args.duration:
                key = keyboard.read_key()
                if key:
                    now_ns = time.time_ns()
                    if key.lower() == "q":
                        break
                    new_label = labels[int(key) - 1] if key.isdigit() and 1 <= int(key) <= len(labels) else None
                    if key == " " or new_label is not None:
                        if active is not None:
                            label_intervals.append(
                                {
                                    "label": active.label,
                                    "start_host_time_ns": active.start_time_ns,
                                    "end_host_time_ns": now_ns,
                                }
                            )
                        active = ActiveLabel(new_label, now_ns) if new_label else None
                        print(f"\nActive label: {active.label if active else 'unlabeled'}")

                raw = device.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                host_time_ns = time.time_ns()
                try:
                    parsed = parse_line(raw)
                except (TypeError, ValueError) as error:
                    write_json_line(
                        sensor_handle,
                        {"host_time_ns": host_time_ns, "type": "parse_error", "error": str(error), "raw_line": raw},
                    )
                    continue

                if isinstance(parsed, FsrImuFrame):
                    frame_count += 1
                    write_json_line(sensor_handle, {"host_time_ns": host_time_ns, **parsed.to_dict()})
                elif isinstance(parsed, dict):
                    status_count += int(parsed.get("type") == "status")
                    write_json_line(sensor_handle, {"host_time_ns": host_time_ns, **parsed})
    except KeyboardInterrupt:
        print()
    finally:
        stopped_ns = time.time_ns()
        if active is not None:
            label_intervals.append(
                {
                    "label": active.label,
                    "start_host_time_ns": active.start_time_ns,
                    "end_host_time_ns": stopped_ns,
                }
            )
        labels_path = episode_dir / "labels.jsonl"
        labels_path.write_text(
            "".join(json.dumps(interval, separators=(",", ":")) + "\n" for interval in label_intervals),
            encoding="utf-8",
        )
        summary = {
            "sensor_frames": frame_count,
            "serial_status_messages": status_count,
            "label_intervals": len(label_intervals),
            "duration_s": time.monotonic() - started,
        }
        (episode_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Saved {frame_count} frames and {len(label_intervals)} label intervals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
