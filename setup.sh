#!/usr/bin/env bash
# ============================================================
# CarbonTrace — One-command setup script
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo ""
echo "🌿 CarbonTrace Setup"
echo "──────────────────────────────────────"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Please install from https://python.org"
  exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✅ Python $PYTHON_VERSION found"

# Create venv
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "🗄  Initializing database..."
python3 -c "from app import create_app; from extensions import db; app = create_app(); 
with app.app_context(): db.create_all(); print('   Database ready.')"

echo "🌱 Seeding demo data..."
python3 seed_demo.py

echo ""
echo "──────────────────────────────────────"
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  cd backend && source venv/bin/activate && python app.py"
echo ""
echo "Then open: http://localhost:5000"
echo ""
echo "Demo account:"
echo "  Email:    demo@carbontrace.app"
echo "  Password: demo1234"
echo "──────────────────────────────────────"
