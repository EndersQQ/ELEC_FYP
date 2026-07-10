#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SO101_DIR = Path(__file__).resolve().parents[2]
SOFTWARE_DIR = SO101_DIR / "software"
sys.path.insert(0, str(SOFTWARE_DIR / "host"))

from so101_sensing.camera import (  # noqa: E402
    CameraConfig,
    capture_snapshot,
    import_cv2,
    list_video_devices,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a UVC camera for SO-101 setup recording.")
    parser.add_argument("--list", action="store_true", help="List /dev/video* devices and exit.")
    parser.add_argument("--device", default="/dev/video0", help="Camera device, for example /dev/video0.")
    parser.add_argument("--name", default="setup", help="Logical camera name.")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--capture", action="store_true", help="Capture one image and write metadata.")
    parser.add_argument("--preview", action="store_true", help="Open a live preview window. Press q to quit.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.list:
        for device in list_video_devices():
            print(device)
        return 0

    config = CameraConfig(args.name, args.device, args.width, args.height, args.fps)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output = args.output or SO101_DIR / "data" / "raw" / "camera_checks" / f"{config.name}_{timestamp}.jpg"

    if args.capture or not args.preview:
        frame = capture_snapshot(config, output)
        metadata_path = output.with_suffix(".json")
        metadata_path.write_text(json.dumps({"camera": config.to_dict(), "frame": frame.to_dict()}, indent=2) + "\n")
        print(f"Captured {output}")
        print(f"Metadata {metadata_path}")

    if args.preview:
        cv2 = import_cv2()
        capture = cv2.VideoCapture(config.device)
        if not capture.isOpened():
            raise SystemExit(f"Could not open camera {config.name} at {config.device}")
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise SystemExit(f"Camera {config.name} stopped returning frames")
                cv2.imshow(f"SO-101 camera: {config.name}", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            capture.release()
            cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
