#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Any

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing import FsrImuFrame, parse_line  # noqa: E402
from so101_sensing.camera import CameraConfig, CameraFrame, import_cv2, open_capture, parse_camera_spec  # noqa: E402

try:
    import serial
except ImportError:
    serial = None  # type: ignore


class JsonlWriter:
    def __init__(self, path: Path):
        self.lock = threading.Lock()
        self.handle = path.open("w", encoding="utf-8")

    def write(self, payload: dict[str, Any]) -> None:
        with self.lock:
            self.handle.write(json.dumps(payload) + "\n")
            self.handle.flush()

    def close(self) -> None:
        with self.lock:
            self.handle.close()


class CameraRecorder(threading.Thread):
    def __init__(
        self,
        config: CameraConfig,
        episode_dir: Path,
        writer: JsonlWriter,
        stop_event: threading.Event,
        status_queue: queue.Queue[str],
        image_format: str,
    ):
        super().__init__(daemon=True)
        self.config = config
        self.episode_dir = episode_dir
        self.writer = writer
        self.stop_event = stop_event
        self.status_queue = status_queue
        self.image_format = image_format
        self.frame_count = 0
        self.first_frame_event = threading.Event()

    def run(self) -> None:
        cv2 = import_cv2()
        camera_dir = self.episode_dir / "cameras" / self.config.name
        camera_dir.mkdir(parents=True, exist_ok=True)

        try:
            capture = open_capture(self.config)
        except Exception as error:
            self.status_queue.put(f"camera_error,{self.config.name},{error}")
            self.stop_event.set()
            return

        frame_interval = 1.0 / self.config.fps if self.config.fps > 0 else 0.0
        next_frame_time = time.monotonic()

        try:
            while not self.stop_event.is_set():
                ok, frame = capture.read()
                if not ok:
                    self.status_queue.put(f"camera_error,{self.config.name},read_failed")
                    self.stop_event.set()
                    break

                now = time.monotonic()
                if now < next_frame_time:
                    time.sleep(min(0.002, next_frame_time - now))
                    continue
                next_frame_time = now + frame_interval

                sequence = self.frame_count
                rel_path = Path("cameras") / self.config.name / f"frame_{sequence:06d}.{self.image_format}"
                output_path = self.episode_dir / rel_path
                if not cv2.imwrite(str(output_path), frame):
                    self.status_queue.put(f"camera_error,{self.config.name},write_failed")
                    self.stop_event.set()
                    break

                height, width = frame.shape[:2]
                frame_record = CameraFrame(
                    camera=self.config.name,
                    sequence=sequence,
                    host_time_ns=time.time_ns(),
                    monotonic_ns=time.monotonic_ns(),
                    path=str(rel_path),
                    width=width,
                    height=height,
                )
                self.writer.write(frame_record.to_dict())
                self.frame_count += 1
                if self.frame_count == 1:
                    self.status_queue.put(f"camera_first_frame,{self.config.name},{width}x{height}")
                    self.first_frame_event.set()
        finally:
            capture.release()


class SerialRecorder(threading.Thread):
    def __init__(
        self,
        port: str,
        baud: int,
        writer: JsonlWriter,
        stop_event: threading.Event,
        status_queue: queue.Queue[str],
    ):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.writer = writer
        self.stop_event = stop_event
        self.status_queue = status_queue
        self.frame_count = 0
        self.status_count = 0

    def run(self) -> None:
        if serial is None:
            self.status_queue.put("serial_error,pyserial_missing")
            self.stop_event.set()
            return

        try:
            device = serial.Serial(self.port, self.baud, timeout=1)
        except Exception as error:
            self.status_queue.put(f"serial_error,{error}")
            self.stop_event.set()
            return

        with device:
            self.status_queue.put(f"serial_connected,{self.port},{self.baud}")
            while not self.stop_event.is_set():
                raw = device.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue

                host_time_ns = time.time_ns()
                parsed = parse_line(raw)
                if isinstance(parsed, FsrImuFrame):
                    self.frame_count += 1
                    self.writer.write({"host_time_ns": host_time_ns, **parsed.to_dict()})
                elif isinstance(parsed, dict):
                    if parsed.get("type") == "status":
                        self.status_count += 1
                    self.writer.write({"host_time_ns": host_time_ns, **parsed})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record a synchronized SO-101 setup episode with camera frames and optional FSR/IMU serial data."
    )
    parser.add_argument(
        "--camera",
        action="append",
        default=[],
        metavar="NAME=DEVICE",
        help=(
            "Camera mapping. Use once for setup, twice later for IMX335: "
            "--camera gripper=/dev/video0 --camera table=/dev/video2"
        ),
    )
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=15.0, help="Capture FPS per camera.")
    parser.add_argument("--serial-port", default=None, help="ESP32 serial port, for example /dev/ttyUSB0.")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds to record. 0 means until Ctrl+C.")
    parser.add_argument("--startup-timeout", type=float, default=10.0, help="Seconds to wait for each camera's first frame.")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--image-format", choices=["jpg", "png"], default="jpg")
    return parser.parse_args()


def build_camera_configs(args: argparse.Namespace) -> list[CameraConfig]:
    specs = args.camera or ["setup=/dev/video0"]
    configs = []
    for index, spec in enumerate(specs):
        config = parse_camera_spec(spec, default_name=f"camera_{index}")
        configs.append(
            CameraConfig(
                name=config.name,
                device=config.device,
                width=args.width,
                height=args.height,
                fps=args.fps,
            )
        )
    return configs


def main() -> int:
    import_cv2()
    args = parse_args()
    cameras = build_camera_configs(args)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    episode_dir = args.output or SO101_DIR / "data" / "raw" / f"episode_{timestamp}"
    episode_dir.mkdir(parents=True, exist_ok=False)

    metadata = {
        "created_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host_time_ns": time.time_ns(),
        "duration_s": args.duration,
        "serial": {"port": args.serial_port, "baud": args.baud, "enabled": bool(args.serial_port)},
        "cameras": [camera.to_dict() for camera in cameras],
        "notes": [
            "Host timestamps are used to align serial frames and camera frames.",
            "The setup camera can be replaced by gripper/table IMX335 cameras using two --camera arguments.",
        ],
    }
    (episode_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    stop_event = threading.Event()
    status_queue: queue.Queue[str] = queue.Queue()
    camera_writer = JsonlWriter(episode_dir / "camera_frames.jsonl")
    sensor_writer = JsonlWriter(episode_dir / "sensor.jsonl")

    workers: list[threading.Thread] = [
        CameraRecorder(camera, episode_dir, camera_writer, stop_event, status_queue, args.image_format)
        for camera in cameras
    ]

    serial_worker = None
    if args.serial_port:
        serial_worker = SerialRecorder(args.serial_port, args.baud, sensor_writer, stop_event, status_queue)
        workers.append(serial_worker)

    print(f"Recording episode -> {episode_dir}")
    print("Waiting for first camera frame. Press Ctrl+C to stop.")
    for worker in workers:
        worker.start()

    try:
        startup_started = time.monotonic()
        camera_workers = [worker for worker in workers if isinstance(worker, CameraRecorder)]
        while camera_workers and not all(worker.first_frame_event.is_set() for worker in camera_workers):
            try:
                status = status_queue.get(timeout=0.25)
                print(status)
            except queue.Empty:
                pass

            if stop_event.is_set():
                break
            if args.startup_timeout > 0 and time.monotonic() - startup_started >= args.startup_timeout:
                missing = [worker.config.name for worker in camera_workers if not worker.first_frame_event.is_set()]
                print(f"camera_error,startup_timeout,{','.join(missing)}")
                stop_event.set()
                break

        started = time.monotonic()
        if not stop_event.is_set():
            print("Recording active. Press Ctrl+C to stop.")

        while not stop_event.is_set():
            try:
                status = status_queue.get(timeout=0.25)
                print(status)
            except queue.Empty:
                pass

            if args.duration > 0 and time.monotonic() - started >= args.duration:
                stop_event.set()
    except KeyboardInterrupt:
        print()
        stop_event.set()
    finally:
        for worker in workers:
            worker.join(timeout=3)
        camera_writer.close()
        sensor_writer.close()

    summary = {
        "camera_frames": {
            worker.config.name: worker.frame_count for worker in workers if isinstance(worker, CameraRecorder)
        },
        "serial_frames": serial_worker.frame_count if serial_worker else 0,
        "serial_status_messages": serial_worker.status_count if serial_worker else 0,
    }
    (episode_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
