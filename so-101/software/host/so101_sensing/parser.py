from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SENSOR_GRID_POSITIONS = {
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
class SensorPoint:
    sensor: int
    raw: int
    percent: int
    x: float
    y: float

    @property
    def connected(self) -> bool:
        return self.raw >= 0 and self.percent >= 0


@dataclass(frozen=True)
class ImuSample:
    available: bool
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    temp_c: float


@dataclass(frozen=True)
class FsrImuFrame:
    schema: int
    sequence: int
    device_ms: int
    dt_ms: int
    connected_count: int
    sensors: list[SensorPoint]
    imu: ImuSample
    raw_line: str

    @property
    def total_pressure(self) -> int:
        return sum(sensor.percent for sensor in self.sensors if sensor.connected)

    @property
    def active_count(self) -> int:
        return sum(1 for sensor in self.sensors if sensor.connected and sensor.percent > 0)

    @property
    def strongest_sensor(self) -> SensorPoint | None:
        connected = [sensor for sensor in self.sensors if sensor.connected]
        return max(connected, key=lambda sensor: sensor.percent, default=None)

    @property
    def contact_centroid(self) -> tuple[float, float] | None:
        total = self.total_pressure
        if total <= 0:
            return None

        x = sum(sensor.x * sensor.percent for sensor in self.sensors if sensor.connected) / total
        y = sum(sensor.y * sensor.percent for sensor in self.sensors if sensor.connected) / total
        return (x, y)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        centroid = self.contact_centroid
        payload["features"] = {
            "total_pressure": self.total_pressure,
            "active_count": self.active_count,
            "contact_centroid": list(centroid) if centroid else None,
            "strongest_sensor": self.strongest_sensor.sensor if self.strongest_sensor else None,
        }
        return payload


def parse_line(line: str) -> FsrImuFrame | dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None

    parts = line.split(",")
    kind = parts[0]

    if kind == "STATUS":
        return {"type": "status", "state": parts[1] if len(parts) > 1 else "", "fields": parts[2:], "raw_line": line}

    if kind == "FRAME":
        return _parse_frame(parts, line)

    return {"type": "unknown", "raw_line": line}


def _parse_frame(parts: list[str], line: str) -> FsrImuFrame | None:
    if len(parts) < 32:
        return None

    schema = int(parts[1])
    if schema != 1:
        raise ValueError(f"Unsupported FRAME schema: {schema}")

    sensors = []
    for sensor_number in range(1, 10):
        raw = int(parts[6 + (sensor_number - 1) * 2])
        percent = int(parts[7 + (sensor_number - 1) * 2])
        x, y = SENSOR_GRID_POSITIONS[sensor_number]
        sensors.append(SensorPoint(sensor_number, raw, percent, x, y))

    imu = ImuSample(
        available=int(parts[24]) == 1,
        accel_x=float(parts[25]),
        accel_y=float(parts[26]),
        accel_z=float(parts[27]),
        gyro_x=float(parts[28]),
        gyro_y=float(parts[29]),
        gyro_z=float(parts[30]),
        temp_c=float(parts[31]),
    )

    return FsrImuFrame(
        schema=schema,
        sequence=int(parts[2]),
        device_ms=int(parts[3]),
        dt_ms=int(parts[4]),
        connected_count=int(parts[5]),
        sensors=sensors,
        imu=imu,
        raw_line=line,
    )
