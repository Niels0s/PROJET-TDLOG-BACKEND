#!/usr/bin/env bash
set -euo pipefail

# Lightweight, idempotent starter for the backend.
# - Creates a local .venv if missing
# - Upgrades pip tools
# - Installs requirements (fast if already installed)
# - Runs uvicorn using the venv's python to avoid PEP 668 / system pip issues

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# If a venv is already activated, prefer it. Otherwise use ./ .venv
if [ -n "${VIRTUAL_ENV-}" ]; then
  VENV_DIR="$VIRTUAL_ENV"
else
  VENV_DIR=".venv"
fi

PYTHON_BIN="${VENV_DIR}/bin/python"

# If the chosen python binary is missing, create a local venv (only when not using an already-activated venv)
if [ ! -x "$PYTHON_BIN" ]; then
  if [ -n "${VIRTUAL_ENV-}" ]; then
    echo "Activated virtualenv at $VENV_DIR but $PYTHON_BIN is missing or not executable." >&2
    echo "Please ensure the activated venv is valid or deactivate it and let this script create .venv." >&2
    exit 1
  else
    echo "Creating virtualenv in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    PYTHON_BIN="${VENV_DIR}/bin/python"
  fi
fi

echo "Using Python: $($PYTHON_BIN --version 2>&1)"

# Ensure pip/tools up to date
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

# Install requirements (will skip already-satisfied packages)
if [ -f requirements.txt ]; then
  echo "Installing requirements from requirements.txt..."
  "$PYTHON_BIN" -m pip install -r requirements.txt
else
  echo "No requirements.txt found — ensure dependencies are installed manually." >&2
fi

echo "Starting uvicorn (app.main:app) on port 8000..."
exec "$PYTHON_BIN" -m uvicorn app.main:app --reload --port 8000
