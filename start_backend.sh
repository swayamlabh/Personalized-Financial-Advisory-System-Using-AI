#!/bin/bash
# ==========================================
#  AI Financial Advisor — Backend Startup
#  For Linux / WSL / macOS
#  Server: http://localhost:8000
#  API Docs: http://localhost:8000/docs
# ==========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv_linux"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "======================================"
echo "  Starting AI Financial Advisor"
echo "  Server: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "======================================"
echo ""

# Create Linux venv if it doesn't exist
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "[Setup] Creating Linux virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "[Error] Failed to create virtual environment. Make sure python3-venv is installed."
        exit 1
    fi
    echo "[Setup] Installing dependencies..."
    "$VENV_DIR/bin/pip" install --quiet fastapi uvicorn scikit-learn pandas numpy pydantic joblib
    echo "[Setup] ✅ Dependencies installed."
fi

echo "[Backend] Starting server..."
cd "$BACKEND_DIR"
"$VENV_DIR/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
