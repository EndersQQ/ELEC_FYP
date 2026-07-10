from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CameraConfig:
    name: str
    device: str
    width: int = 1280
    height: int = 720
    fps: float = 30.0
    fourcc: str = "MJPG"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CameraFrame:
    camera: str
    sequence: int
    host_time_ns: int
    monotonic_ns: int
    path: str
    width: int
    height: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_video_devices() -> list[str]:
    return [str(path) for path in sorted(Path("/dev").glob("video*"))]


def parse_camera_spec(spec: str, default_name: str = "setup") -> CameraConfig:
    if "=" in spec:
        name, device = spec.split("=", 1)
        name = name.strip()
        device = device.strip()
    else:
        name = default_name
        device = spec.strip()

    if not name:
        raise ValueError(f"Camera spec has an empty name: {spec!r}")
    if not device:
        raise ValueError(f"Camera spec has an empty device: {spec!r}")

    return CameraConfig(name=name, device=device)


def import_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as error:
        raise SystemExit(
            "opencv-python is required for camera tools. "
            "Run: ./scripts/setup_camera_ml_env.sh"
        ) from error
    return cv2


def open_capture(config: CameraConfig):
    cv2 = import_cv2()
    capture = cv2.VideoCapture(config.device)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open camera {config.name} at {config.device}")

    if config.fourcc:
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*config.fourcc[:4]))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
    capture.set(cv2.CAP_PROP_FPS, config.fps)
    return capture


def capture_snapshot(config: CameraConfig, output: Path) -> CameraFrame:
    import time

    cv2 = import_cv2()
    capture = open_capture(config)
    try:
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Camera {config.name} opened but did not return a frame")

        output.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(output), frame):
            raise RuntimeError(f"Could not write camera snapshot to {output}")

        height, width = frame.shape[:2]
        return CameraFrame(
            camera=config.name,
            sequence=0,
            host_time_ns=time.time_ns(),
            monotonic_ns=time.monotonic_ns(),
            path=str(output),
            width=width,
            height=height,
        )
    finally:
        capture.release()
