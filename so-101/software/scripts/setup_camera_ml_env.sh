#!/usr/bin/env bash
set -euo pipefail

SO101_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOFTWARE_DIR="${SO101_DIR}/software"
VENV_DIR="${SOFTWARE_DIR}/.venv"

python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "${SOFTWARE_DIR}/requirements-ml.txt"

cat <<EOF

Camera/ML environment ready.

Activate it with:
  source ${VENV_DIR}/bin/activate

Quick camera check:
  python software/tools/check_camera.py --list
  python software/tools/check_camera.py --device /dev/video0 --capture

Record a setup episode:
  python software/tools/record_multimodal_episode.py --camera setup=/dev/video0 --duration 10
EOF
