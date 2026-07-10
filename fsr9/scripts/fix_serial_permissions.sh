#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${SUDO_USER:-${USER}}"

sudo usermod -a -G dialout "$USER_NAME"

echo "Added $USER_NAME to dialout."
echo "Log out and log back in, or reboot, before uploading again."
