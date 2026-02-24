#!/usr/bin/env bash
set -euo pipefail
while true; do
  /mnt/chromeos/MyFiles/Downloads/SHARE/core/mission-control/update_status.py >/dev/null 2>&1 || true
  sleep 45
done
