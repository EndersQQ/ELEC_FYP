from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class VibrationResult:
    active: bool
    impact: bool
    score: float


@dataclass(frozen=True)
class FusionResult:
    state: str
    candidate: str
    vibration: VibrationResult


class VibrationDetector:
    def __init__(
        self,
        accel_rms_threshold: float = 0.35,
        gyro_rms_threshold: float = 8.0,
        impact_peak_to_peak: float = 4.0,
        enter_windows: int = 2,
        release_windows: int = 3,
    ):
        self.accel_rms_threshold = accel_rms_threshold
        self.gyro_rms_threshold = gyro_rms_threshold
        self.impact_peak_to_peak = impact_peak_to_peak
        self.enter_windows = enter_windows
        self.release_windows = release_windows
        self.active = False
        self._enter_count = 0
        self._release_count = 0

    def update(self, features: Mapping[str, float]) -> VibrationResult:
        accel_rms = float(features.get("imu_accel_highpass_rms", 0.0))
        gyro_rms = float(features.get("imu_gyro_highpass_rms", 0.0))
        peak_to_peak = float(features.get("imu_accel_peak_to_peak", 0.0))
        score = max(
            accel_rms / max(self.accel_rms_threshold, 1e-6),
            gyro_rms / max(self.gyro_rms_threshold, 1e-6),
        )
        evidence = score >= 1.0

        if not self.active:
            self._enter_count = self._enter_count + 1 if evidence else 0
            if self._enter_count >= self.enter_windows:
                self.active = True
                self._enter_count = 0
        else:
            self._release_count = self._release_count + 1 if score < 0.65 else 0
            if self._release_count >= self.release_windows:
                self.active = False
                self._release_count = 0

        return VibrationResult(self.active, peak_to_peak >= self.impact_peak_to_peak, score)


class GraspStateMachine:
    def __init__(
        self,
        contact_total_threshold: float = 10.0,
        firm_total_threshold: float = 25.0,
        pressure_change_threshold: float = 8.0,
        centroid_motion_threshold: float = 0.08,
        transition_windows: int = 3,
        vibration_detector: VibrationDetector | None = None,
    ):
        self.contact_total_threshold = contact_total_threshold
        self.firm_total_threshold = firm_total_threshold
        self.pressure_change_threshold = pressure_change_threshold
        self.centroid_motion_threshold = centroid_motion_threshold
        self.transition_windows = transition_windows
        self.vibration_detector = vibration_detector or VibrationDetector()
        self.state = "no_contact"
        self._candidate = self.state
        self._candidate_count = 0

    def _candidate_state(self, features: Mapping[str, float], vibration: VibrationResult) -> str:
        total = float(features.get("fsr_total_mean", 0.0))
        peak = max(float(features.get(f"fsr_s{number}_max", 0.0)) for number in range(1, 10))
        contact = total >= self.contact_total_threshold or peak >= self.contact_total_threshold
        changing = (
            abs(float(features.get("fsr_total_delta", 0.0))) >= self.pressure_change_threshold
            or float(features.get("fsr_centroid_motion_mean", 0.0)) >= self.centroid_motion_threshold
        )

        if vibration.impact:
            return "impact"
        if not contact:
            return "robot_motion" if vibration.active else "no_contact"
        if vibration.active and changing:
            return "slip"
        if vibration.active:
            return "possible_slip"
        if total < self.firm_total_threshold:
            return "touch"
        return "stable_grasp"

    def update(self, features: Mapping[str, float]) -> FusionResult:
        vibration = self.vibration_detector.update(features)
        candidate = self._candidate_state(features, vibration)
        if candidate == self.state:
            self._candidate = candidate
            self._candidate_count = 0
        elif candidate == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = candidate
            self._candidate_count = 1
        if candidate != self.state and self._candidate_count >= self.transition_windows:
            self.state = candidate
            self._candidate_count = 0
        return FusionResult(self.state, candidate, vibration)
