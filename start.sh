#!/usr/bin/env bash
# Quick start script — activates venv and starts Flask dev server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
echo "🌿 Starting CarbonTrace server at http://localhost:5001"
python app.py
