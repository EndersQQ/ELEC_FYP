#!/usr/bin/env python3
"""Check which SO-101 serial ports can see Feetech servo IDs 1..6."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

EXPECTED_IDS = tuple(range(1, 7))
EXPECTED_MODEL = 777


@dataclass
class PortCheck:
    label: str
    port: str
    found: dict[int, int]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and all(self.found.get(id_) == EXPECTED_MODEL for id_ in EXPECTED_IDS)


def make_bus(port: str):
    try:
        from lerobot.motors import Motor, MotorNormMode
        from lerobot.motors.feetech import FeetechMotorsBus
    except ImportError as error:
        raise SystemExit("LeRobot is required. Run this tool from the project's LeRobot environment.") from error

    motors = {
        "shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
        "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
        "elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
        "wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
        "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
        "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
    }
    return FeetechMotorsBus(port=port, motors=motors)


def check_port(label: str, port: str) -> PortCheck:
    if not Path(port).exists():
        return PortCheck(label=label, port=port, found={}, error="device path does not exist")

    bus = make_bus(port)
    try:
        bus.connect(handshake=False)
        found = {}
        for id_ in EXPECTED_IDS:
            model = bus.ping(id_)
            if model is not None:
                found[id_] = model
        return PortCheck(label=label, port=port, found=found)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report the raw failure.
        return PortCheck(label=label, port=port, found={}, error=str(exc).strip())
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


def print_check(check: PortCheck) -> None:
    print(f"{check.label}: {check.port}")
    if check.error:
        print(f"  ERROR: {check.error}")
        return

    if check.found:
        found_text = ", ".join(f"{id_}:{model}" for id_, model in sorted(check.found.items()))
    else:
        found_text = "none"

    missing = [id_ for id_ in EXPECTED_IDS if id_ not in check.found]
    wrong = {id_: model for id_, model in check.found.items() if model != EXPECTED_MODEL}

    print(f"  found id:model: {found_text}")
    if missing:
        print(f"  missing IDs: {', '.join(str(id_) for id_ in missing)}")
    if wrong:
        wrong_text = ", ".join(f"{id_}:{model}" for id_, model in sorted(wrong.items()))
        print(f"  wrong model numbers: {wrong_text}")
    print(f"  SO-101 bus check: {'OK' if check.ok else 'FAILED'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--follower-port", required=True)
    parser.add_argument("--leader-port", required=True)
    args = parser.parse_args()

    print("SO-101 Feetech motor bus check")
    print("Expected IDs: 1, 2, 3, 4, 5, 6")
    print("Expected model number: 777")
    print()

    follower = check_port("Configured follower", args.follower_port)
    leader = check_port("Configured leader", args.leader_port)

    print_check(follower)
    print()
    print_check(leader)
    print()

    if follower.ok and leader.ok:
        print("Both configured ports can see all expected SO-101 motors.")
        return 0

    if not follower.ok and leader.ok:
        print("The configured follower port cannot see the motors, but the configured leader port can.")
        print("Check whether the USB adapters are physically swapped or whether _config.sh has stale roles.")
        return 2

    if not follower.ok and not leader.ok:
        print("Neither configured port can see all follower motor IDs.")
        print("Check follower arm power, servo bus cable direction/seating, and controller-board connection.")
        return 2

    print("The configured follower bus looks OK; investigate leader calibration/connection next.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
