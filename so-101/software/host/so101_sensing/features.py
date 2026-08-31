from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


FEATURE_VERSION = 1
SENSOR_POSITIONS = {
    1: (-1.0, -1.0),
    2: (-1.0, 0.0),
    3: (-1.0, 1.0),
    4: (0.0, -1.0),
    5: (0.0, 0.0),
    6: (0.0, 1.0),
    7: (1.0, -1.0),
    8: (1.0, 0.0),
    9: (1.0, 1.0),
}


@dataclass(frozen=True)
class FeatureWindow:
    start_time_ns: int
    end_time_ns: int
    frames: list[dict[str, Any]]


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _std(values: Sequence[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _series_features(prefix: str, values: Sequence[float], duration_s: float) -> dict[str, float]:
    if not values:
        values = [0.0]
    delta = float(values[-1] - values[0])
    return {
        f"{prefix}_mean": _mean(values),
        f"{prefix}_std": _std(values),
        f"{prefix}_min": float(min(values)),
        f"{prefix}_max": float(max(values)),
        f"{prefix}_last": float(values[-1]),
        f"{prefix}_delta": delta,
        f"{prefix}_slope": delta / max(duration_s, 1e-6),
    }


def _magnitude(x: Sequence[float], y: Sequence[float], z: Sequence[float]) -> list[float]:
    return [math.sqrt(a * a + b * b + c * c) for a, b, c in zip(x, y, z)]


def _rms(values: Sequence[float]) -> float:
    return math.sqrt(_mean([value * value for value in values])) if values else 0.0


def _spectral_features(values: Sequence[float], sample_rate_hz: float) -> dict[str, float]:
    if len(values) < 4 or sample_rate_hz <= 0:
        return {
            "dominant_hz": 0.0,
            "band_1_5_hz": 0.0,
            "band_5_15_hz": 0.0,
            "band_15_80_hz": 0.0,
        }

    centered = [value - _mean(values) for value in values]
    total_energy = sum(value * value for value in centered)
    if total_energy <= 1e-12:
        return {
            "dominant_hz": 0.0,
            "band_1_5_hz": 0.0,
            "band_5_15_hz": 0.0,
            "band_15_80_hz": 0.0,
        }

    energies: list[tuple[float, float]] = []
    count = len(centered)
    for index in range(1, count // 2 + 1):
        frequency = index * sample_rate_hz / count
        real = 0.0
        imaginary = 0.0
        for sample_index, value in enumerate(centered):
            angle = 2.0 * math.pi * index * sample_index / count
            real += value * math.cos(angle)
            imaginary -= value * math.sin(angle)
        energies.append((frequency, real * real + imaginary * imaginary))

    spectral_total = sum(energy for _, energy in energies) or 1.0
    dominant_frequency = max(energies, key=lambda item: item[1])[0]

    def band_energy(low: float, high: float) -> float:
        return sum(energy for frequency, energy in energies if low <= frequency < high) / spectral_total

    return {
        "dominant_hz": dominant_frequency,
        "band_1_5_hz": band_energy(1.0, 5.0),
        "band_5_15_hz": band_energy(5.0, 15.0),
        "band_15_80_hz": band_energy(15.0, 80.0),
    }


def _frame_time_ns(frame: Mapping[str, Any]) -> int | None:
    value = frame.get("host_time_ns")
    return int(value) if value is not None else None


def iter_feature_windows(
    frames: Iterable[dict[str, Any]],
    window_ms: int = 500,
    hop_ms: int = 100,
    minimum_frames: int = 4,
) -> Iterable[FeatureWindow]:
    usable = sorted(
        (frame for frame in frames if _frame_time_ns(frame) is not None and isinstance(frame.get("sensors"), list)),
        key=lambda frame: int(frame["host_time_ns"]),
    )
    if not usable:
        return

    window_ns = int(window_ms * 1_000_000)
    hop_ns = int(hop_ms * 1_000_000)
    start_ns = int(usable[0]["host_time_ns"])
    final_ns = int(usable[-1]["host_time_ns"])
    left = 0
    right = 0

    while start_ns + window_ns <= final_ns:
        end_ns = start_ns + window_ns
        while left < len(usable) and int(usable[left]["host_time_ns"]) < start_ns:
            left += 1
        right = max(right, left)
        while right < len(usable) and int(usable[right]["host_time_ns"]) < end_ns:
            right += 1
        selected = usable[left:right]
        if len(selected) >= minimum_frames:
            yield FeatureWindow(start_ns, end_ns, selected)
        start_ns += hop_ns


def _sample_rate_hz(frames: Sequence[Mapping[str, Any]]) -> float:
    device_times = [int(frame["device_ms"]) for frame in frames if frame.get("device_ms") is not None]
    deltas_ms = [later - earlier for earlier, later in zip(device_times, device_times[1:]) if 0 < later - earlier < 1000]
    if deltas_ms:
        return 1000.0 / statistics.median(deltas_ms)

    host_times = [int(frame["host_time_ns"]) for frame in frames if frame.get("host_time_ns") is not None]
    deltas_s = [(later - earlier) / 1_000_000_000 for earlier, later in zip(host_times, host_times[1:]) if later > earlier]
    return 1.0 / statistics.median(deltas_s) if deltas_s else 0.0


def extract_window_features(frames: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not frames:
        raise ValueError("At least one sensor frame is required")

    first_time = _frame_time_ns(frames[0]) or 0
    last_time = _frame_time_ns(frames[-1]) or first_time
    duration_s = max((last_time - first_time) / 1_000_000_000, 1e-6)
    features: dict[str, float] = {}

    sensor_series: dict[int, list[float]] = {number: [] for number in range(1, 10)}
    totals: list[float] = []
    active_counts: list[float] = []
    centroids_x: list[float] = []
    centroids_y: list[float] = []

    for frame in frames:
        points = {int(point.get("sensor", 0)): point for point in frame.get("sensors", [])}
        values = []
        for sensor_number in range(1, 10):
            point = points.get(sensor_number, {})
            percent = float(point.get("percent", 0.0))
            if percent < 0:
                percent = 0.0
            sensor_series[sensor_number].append(percent)
            values.append(percent)

        total = sum(values)
        totals.append(total)
        active_counts.append(float(sum(value > 0 for value in values)))
        if total > 0:
            centroids_x.append(
                sum(SENSOR_POSITIONS[index + 1][0] * value for index, value in enumerate(values)) / total
            )
            centroids_y.append(
                sum(SENSOR_POSITIONS[index + 1][1] * value for index, value in enumerate(values)) / total
            )
        else:
            centroids_x.append(0.0)
            centroids_y.append(0.0)

    for sensor_number, values in sensor_series.items():
        features.update(_series_features(f"fsr_s{sensor_number}", values, duration_s))
    features.update(_series_features("fsr_total", totals, duration_s))
    features.update(_series_features("fsr_active", active_counts, duration_s))
    features.update(_series_features("fsr_centroid_x", centroids_x, duration_s))
    features.update(_series_features("fsr_centroid_y", centroids_y, duration_s))
    centroid_steps = [
        math.hypot(x2 - x1, y2 - y1)
        for x1, x2, y1, y2 in zip(centroids_x, centroids_x[1:], centroids_y, centroids_y[1:])
    ]
    features["fsr_centroid_motion_mean"] = _mean(centroid_steps)
    features["fsr_centroid_motion_max"] = max(centroid_steps, default=0.0)

    imu_rows = [frame.get("imu", {}) for frame in frames]
    available = [bool(row.get("available", False)) for row in imu_rows]
    features["imu_available_ratio"] = sum(available) / len(available)

    axes: dict[str, list[float]] = {}
    for name in ("accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"):
        axes[name] = [float(row.get(name, 0.0)) if ok else 0.0 for row, ok in zip(imu_rows, available)]
        features[f"imu_{name}_mean"] = _mean(axes[name])
        features[f"imu_{name}_std"] = _std(axes[name])

    acceleration = _magnitude(axes["accel_x"], axes["accel_y"], axes["accel_z"])
    angular_velocity = _magnitude(axes["gyro_x"], axes["gyro_y"], axes["gyro_z"])
    centered_accel_axes = {
        name: [value - _mean(axes[name]) for value in axes[name]]
        for name in ("accel_x", "accel_y", "accel_z")
    }
    centered_gyro_axes = {
        name: [value - _mean(axes[name]) for value in axes[name]]
        for name in ("gyro_x", "gyro_y", "gyro_z")
    }
    acceleration_centered = _magnitude(
        centered_accel_axes["accel_x"], centered_accel_axes["accel_y"], centered_accel_axes["accel_z"]
    )
    gyro_centered = _magnitude(
        centered_gyro_axes["gyro_x"], centered_gyro_axes["gyro_y"], centered_gyro_axes["gyro_z"]
    )
    sample_rate = _sample_rate_hz(frames)
    jerk = (
        [
            math.sqrt(
                sum(
                    ((axes[name][index] - axes[name][index - 1]) * sample_rate) ** 2
                    for name in ("accel_x", "accel_y", "accel_z")
                )
            )
            for index in range(1, len(acceleration))
        ]
        if sample_rate > 0
        else []
    )

    features.update(_series_features("imu_accel_magnitude", acceleration, duration_s))
    features.update(_series_features("imu_gyro_magnitude", angular_velocity, duration_s))
    features["imu_accel_highpass_rms"] = _rms(acceleration_centered)
    features["imu_gyro_highpass_rms"] = _rms(gyro_centered)
    features["imu_accel_peak_to_peak"] = max(
        (
            max(axes[name], default=0.0) - min(axes[name], default=0.0)
            for name in ("accel_x", "accel_y", "accel_z")
        ),
        default=0.0,
    )
    features["imu_gyro_peak_to_peak"] = max(
        (
            max(axes[name], default=0.0) - min(axes[name], default=0.0)
            for name in ("gyro_x", "gyro_y", "gyro_z")
        ),
        default=0.0,
    )
    features["imu_jerk_rms"] = _rms(jerk)
    features["imu_jerk_max"] = max((abs(value) for value in jerk), default=0.0)
    features["imu_sample_rate_hz"] = sample_rate
    most_dynamic_accel_axis = max(centered_accel_axes.values(), key=_std)
    most_dynamic_gyro_axis = max(centered_gyro_axes.values(), key=_std)
    for name, value in _spectral_features(most_dynamic_accel_axis, sample_rate).items():
        features[f"imu_accel_{name}"] = value
    for name, value in _spectral_features(most_dynamic_gyro_axis, sample_rate).items():
        features[f"imu_gyro_{name}"] = value

    return features


def select_feature_names(features: Mapping[str, float], modality: str) -> list[str]:
    if modality not in {"fsr", "imu", "fused"}:
        raise ValueError(f"Unsupported modality: {modality}")
    if modality == "fused":
        return sorted(features)
    prefix = f"{modality}_"
    return sorted(name for name in features if name.startswith(prefix))
