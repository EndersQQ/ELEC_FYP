#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import deque
from pathlib import Path

try:
    import serial
except ImportError as error:
    raise SystemExit("pyserial is required. Install software/requirements.txt first.") from error

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing import (  # noqa: E402
    FsrImuFrame,
    GraspStateMachine,
    SensorClassifier,
    extract_window_features,
    parse_line,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live FSR classification and IMU/grasp-state detection.")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--model", type=Path, default=None, help="Optional trained .joblib artifact.")
    parser.add_argument("--window-ms", type=int, default=500)
    parser.add_argument("--hop-ms", type=int, default=100)
    parser.add_argument("--confidence-threshold", type=float, default=0.6)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON lines.")
    args = parser.parse_args()

    classifier = SensorClassifier.load(args.model, args.confidence_threshold) if args.model else None
    window_ms = classifier.window_ms if classifier else args.window_ms
    hop_ms = classifier.hop_ms if classifier else args.hop_ms
    frames: deque[dict] = deque()
    state_machine = GraspStateMachine()
    last_prediction_ns = 0

    print(f"Reading {args.port} at {args.baud} baud. Press Ctrl+C to stop.", file=sys.stderr)
    try:
        with serial.Serial(args.port, args.baud, timeout=1) as device:
            while True:
                raw = device.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                host_time_ns = time.time_ns()
                try:
                    parsed = parse_line(raw)
                except (TypeError, ValueError) as error:
                    print(f"parse_error: {error}", file=sys.stderr)
                    continue
                if not isinstance(parsed, FsrImuFrame):
                    continue

                frames.append({"host_time_ns": host_time_ns, **parsed.to_dict()})
                cutoff_ns = host_time_ns - window_ms * 1_000_000
                while frames and int(frames[0]["host_time_ns"]) < cutoff_ns:
                    frames.popleft()
                if host_time_ns - last_prediction_ns < hop_ms * 1_000_000:
                    continue
                if len(frames) < 4 or int(frames[-1]["host_time_ns"]) - int(frames[0]["host_time_ns"]) < (
                    window_ms - 50
                ) * 1_000_000:
                    continue

                last_prediction_ns = host_time_ns
                features = extract_window_features(list(frames))
                fusion = state_machine.update(features)
                prediction = classifier.predict_features(features) if classifier else None
                payload = {
                    "host_time_ns": host_time_ns,
                    "state": fusion.state,
                    "candidate": fusion.candidate,
                    "vibration_active": fusion.vibration.active,
                    "vibration_score": round(fusion.vibration.score, 3),
                    "impact": fusion.vibration.impact,
                    "total_pressure": round(features["fsr_total_mean"], 2),
                    "model_label": prediction.label if prediction else None,
                    "model_confidence": round(prediction.confidence, 4) if prediction else None,
                    "probabilities": prediction.probabilities if prediction else None,
                }
                if args.json:
                    print(json.dumps(payload, separators=(",", ":")), flush=True)
                else:
                    model_text = (
                        f" model={prediction.label} ({prediction.confidence:.0%})" if prediction else ""
                    )
                    print(
                        f"state={fusion.state:<14} candidate={fusion.candidate:<14} "
                        f"pressure={features['fsr_total_mean']:6.1f} vibration={fusion.vibration.score:5.2f}{model_text}",
                        flush=True,
                    )
    except KeyboardInterrupt:
        print(file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
