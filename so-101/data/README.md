# Data

Local experiment outputs live here. Raw and processed data are ignored by Git.

Camera test snapshots:

```text
so-101/data/raw/camera_checks/
```

Recorded episodes:

```text
so-101/data/raw/episode_YYYYMMDD_HHMMSS/
```

Trained models and processed datasets:

```text
so-101/data/processed/
```

The main episode recorder writes:

```text
metadata.json
summary.json
sensor.jsonl
camera_frames.jsonl
cameras/<camera-name>/*.jpg
```

The labeled sensor recorder writes:

```text
metadata.json
summary.json
sensor.jsonl
labels.jsonl
```

Label intervals and sensor frames remain raw inputs. `build_sensor_dataset.py` writes derived feature windows under `data/processed/`.
