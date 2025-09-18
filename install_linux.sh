#!/usr/bin/env bash
set -euo pipefail

CREATE_DB=0
if [[ "${1:-}" == "--with-db" ]]; then
  CREATE_DB=1
fi

echo "📦 Creating environment..."
python3 -m venv env

echo "📦 Activating environment..."
# activate for the current shell
# (shellcheck disable=SC1091)
source env/bin/activate

echo "📦 Upgrading pip in venv..."
python -m pip install --upgrade pip

echo "📦 Installing Chat Server Demo (no deps) into venv..."
pip install . --no-deps

echo "📦 Installing core dependencies into venv..."
pip install streamlit pyyaml azure-identity azure-keyvault-secrets sqlalchemy pyodbc

if [[ $CREATE_DB -eq 1 ]]; then
  echo "🗄️  Creating database..."
  python -m chat_server_demo.database.create_db
fi

echo "✅ Installation complete."
