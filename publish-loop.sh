#!/bin/bash
# publish-loop.sh - Updates Mission Control status and pushes to GitHub Pages

set -e

# Change to the directory where the script is located
cd "$(dirname "$0")"

while true; do
  echo "[$(date)] Updating status..."
  
  # Run python scripts to update JSONs
  python3 update_status.py
  # Run system status update if available (assuming it works similarly)
  if [ -f "update_system_status.py" ]; then
    python3 update_system_status.py
  fi

  # Check if files changed
  if git status --porcelain | grep -q 'json'; then
    echo "Changes detected. Committing and pushing..."
    git add status.json system-status.json usage-history.jsonl
    git commit -m "Update status: $(date)"
    git push origin gh-pages
  else
    echo "No changes."
  fi

  echo "Sleeping for 60 seconds..."
  sleep 60
done
