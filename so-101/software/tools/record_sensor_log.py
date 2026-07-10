#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

try:
    import serial
except ImportError as error:
    raise SystemExit("pyserial is required. Install it with: python3 -m pip install pyserial") from error

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing import FsrImuFrame, parse_line  # noqa: E402


def frame_to_csv_row(frame: FsrImuFrame, host_time_ns: int) -> dict[str, object]:
    centroid = frame.contact_centroid
    strongest = frame.strongest_sensor
    row: dict[str, object] = {
        "host_time_ns": host_time_ns,
        "schema": frame.schema,
        "sequence": frame.sequence,
        "device_ms": frame.device_ms,
        "dt_ms": frame.dt_ms,
        "connected_count": frame.connected_count,
        "total_pressure": frame.total_pressure,
        "active_count": frame.active_count,
        "centroid_x": "" if centroid is None else centroid[0],
        "centroid_y": "" if centroid is None else centroid[1],
        "strongest_sensor": "" if strongest is None else strongest.sensor,
        "strongest_percent": "" if strongest is None else strongest.percent,
        "imu_available": int(frame.imu.available),
        "accel_x": frame.imu.accel_x,
        "accel_y": frame.imu.accel_y,
        "accel_z": frame.imu.accel_z,
        "gyro_x": frame.imu.gyro_x,
        "gyro_y": frame.imu.gyro_y,
        "gyro_z": frame.imu.gyro_z,
        "temp_c": frame.imu.temp_c,
    }

    for sensor in frame.sensors:
        row[f"s{sensor.sensor}_raw"] = sensor.raw
        row[f"s{sensor.sensor}_percent"] = sensor.percent

    return row


def csv_fieldnames() -> list[str]:
    fields = [
        "host_time_ns",
        "schema",
        "sequence",
        "device_ms",
        "dt_ms",
        "connected_count",
        "total_pressure",
        "active_count",
        "centroid_x",
        "centroid_y",
        "strongest_sensor",
        "strongest_percent",
        "imu_available",
        "accel_x",
        "accel_y",
        "accel_z",
        "gyro_x",
        "gyro_y",
        "gyro_z",
        "temp_c",
    ]
    for sensor_number in range(1, 10):
        fields.extend([f"s{sensor_number}_raw", f"s{sensor_number}_percent"])
    return fields


def open_output(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8", newline="")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record ESP32-S3 FSR/IMU frames for SO-101 grasping experiments.")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds to record. 0 means until Ctrl+C.")
    args = parser.parse_args()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output = args.output or SO101_DIR / "data" / "raw" / f"fsr_imu_{timestamp}.{args.format}"

    frame_count = 0
    status_count = 0
    started = time.monotonic()

    with serial.Serial(args.port, args.baud, timeout=1) as device, open_output(output) as handle:
        writer = None
        if args.format == "csv":
            writer = csv.DictWriter(handle, fieldnames=csv_fieldnames())
            writer.writeheader()

        print(f"Recording {args.port} at {args.baud} baud -> {output}")
        try:
            while args.duration <= 0 or time.monotonic() - started < args.duration:
                raw = device.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue

                host_time_ns = time.time_ns()
                parsed = parse_line(raw)

                if isinstance(parsed, FsrImuFrame):
                    frame_count += 1
                    if args.format == "jsonl":
                        handle.write(json.dumps({"host_time_ns": host_time_ns, **parsed.to_dict()}) + "\n")
                    else:
                        assert writer is not None
                        writer.writerow(frame_to_csv_row(parsed, host_time_ns))
                elif isinstance(parsed, dict) and parsed.get("type") == "status":
                    status_count += 1
                    if args.format == "jsonl":
                        handle.write(json.dumps({"host_time_ns": host_time_ns, **parsed}) + "\n")

                if frame_count and frame_count % 100 == 0:
                    print(f"{frame_count} frames recorded")
        except KeyboardInterrupt:
            print()

    print(f"Done. {frame_count} frames, {status_count} status messages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
