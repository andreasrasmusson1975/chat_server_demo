#!/usr/bin/env bash
set -euo pipefail

echo "📦 Creating environment..."
python3 -m venv env

echo "📦 Activating environment..."
# activate for the current shell
source env/bin/activate

echo "📦 Upgrading pip in venv..."
python -m pip install --upgrade pip

echo "📦 Installing Chat Server Demo (no deps) into venv..."
pip install . --no-deps

echo "📦 Installing core dependencies into venv..."
pip install streamlit pyyaml

echo "✅ Installation complete."
