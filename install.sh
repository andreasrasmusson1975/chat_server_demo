#!/usr/bin/env bash

# ---------------------------------------------
# Chat Server Demo Installation Script
#
# This script automates the setup and configuration of the MPAI Assistant
# chat server demo. It creates a Python virtual environment, installs
# dependencies, and configures the database and application secrets.
#
# Usage:
#   ./install.sh --sql-server FQDN --db-name NAME \
#       --db-password-secret SECRET --app-user-secret SECRET \
#       --vault-name VAULT --domain HOST [--fresh] [--venv DIR] [--with-db]
#
# Options:
#   --sql-server FQDN            Fully qualified domain name of the SQL server
#   --db-name NAME               Name of the database to configure
#   --db-password-secret SECRET  Secret name for the database password
#   --app-user-secret SECRET     Secret name for the application user credentials
#   --vault-name VAULT           Name of the Azure Key Vault
#   --domain HOST                Domain name for the application
#   --with-db                    Initialize and migrate the database schema
#   --fresh                      Recreate the virtual environment from scratch
#   --venv DIR                   Specify a custom directory for the virtual environment
#   -h, --help                   Display this help message
#
# Notes:
# - Ensure that the required secrets are stored in Azure Key Vault.
# - Run this script with appropriate permissions to access the Key Vault and configure the database.
# - The script uses Python 3 by default but allows customization via the PYTHON_BIN environment variable.
#
# Author: Andreas Rasmusson
# ---------------------------------------------

# Variables and defaults
set -Eeuo pipefail
IFS=$'\n\t'
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="env"
FRESH=0
WITH_DB=0
SQL_SERVER=""
DB_NAME=""
DB_PASS_SECRET=""
APP_USER_SECRET=""
VAULT_NAME=""
DOMAIN=""

# iterate args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fresh) FRESH=1; shift ;;
    --venv)  VENV_DIR="${2:?Missing venv path}"; shift 2 ;;
    --sql-server)  SQL_SERVER="${2:?Missing FQDN}"; shift 2 ;;
    --db-name)     DB_NAME="${2:?Missing DB name}"; shift 2 ;;
    --db-password-secret) DB_PASS_SECRET="${2:?Missing DB password secret name}"; shift 2 ;;
    --app-user-secret)    APP_USER_SECRET="${2:?Missing app user secret name}"; shift 2 ;;
    --vault-name)  VAULT_NAME="${2:?Missing vault name}"; shift 2 ;;
    --domain)      DOMAIN="${2:?Missing domain}"; shift 2 ;;
    --with-db)     WITH_DB=1; shift ;;
    -h|--help)
      echo "Usage: $0 --sql-server FQDN --db-name NAME --db-password-secret SECRET --app-user-secret SECRET --vault-name VAULT --domain HOST [--fresh] [--venv DIR] [--with-db]"
      exit 0
      ;;
    *) echo "❌ Unknown arg: $1"; exit 1 ;;
  esac
done

# Validate required args
[[ -n "$SQL_SERVER" ]]   || { echo "❌ Missing --sql-server"; exit 1; }
[[ -n "$DB_NAME" ]]      || { echo "❌ Missing --db-name"; exit 1; }
[[ -n "$DB_PASS_SECRET" ]] || { echo "❌ Missing --db-password-secret"; exit 1; }
[[ -n "$APP_USER_SECRET" ]] || { echo "❌ Missing --app-user-secret"; exit 1; }
[[ -n "$VAULT_NAME" ]]   || { echo "❌ Missing --vault-name"; exit 1; }
[[ -n "$DOMAIN" ]]       || { echo "❌ Missing --domain"; exit 1; }

# export envs
export CHAT_SERVER_DEMO_AZURE_SQL_SERVER="${SQL_SERVER}"
export CHAT_SERVER_DEMO_DB_NAME="${DB_NAME}"
export CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME="${DB_PASS_SECRET}"
export CHAT_SERVER_DEMO_APP_USER_SECRET_NAME="${APP_USER_SECRET}"
export AZURE_KEY_VAULT_URL="https://${VAULT_NAME}.vault.azure.net"

msg() { echo -e "👉 $*"; }

# -------------------------------
# System prerequisites
# -------------------------------
msg "📦 Installing prerequisites…"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-dev build-essential ca-certificates nginx

# -------------------------------
# Virtual environment
# -------------------------------
if [[ $FRESH -eq 1 && -d "$VENV_DIR" ]]; then
  msg "Removing existing venv $VENV_DIR"
  rm -rf "$VENV_DIR"
fi
if [[ ! -d "$VENV_DIR" ]]; then
  msg "Creating venv $VENV_DIR"
  "${PYTHON_BIN}" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

msg "Upgrading pip…"
python -m pip install --upgrade pip setuptools wheel

msg "Installing package…"
pip install . --no-deps

msg "Installing runtime deps…"
pip install streamlit azure-identity azure-keyvault-secrets sqlalchemy pyodbc pyyaml

# -------------------------------
# Database setup (optional)
# -------------------------------
if [[ $WITH_DB -eq 1 ]]; then
  msg "🗄️ Setting up database schema…"
  python -m chat_server_demo.database.init_schema
fi

# -------------------------------
# Streamlit config
# -------------------------------
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml <<EOF
[server]
enableCORS = false
enableXsrfProtection = false
headless = true
port = 8501
address = "0.0.0.0"
baseUrlPath = "/app"
EOF

# -------------------------------
# Systemd service
# -------------------------------
SERVICE_FILE=/etc/systemd/system/chat_server_demo_app.service
APP_DIR=$(pwd)
STREAMLIT_BIN="${APP_DIR}/${VENV_DIR}/bin/streamlit"

msg "🛠️  Creating systemd service…"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Chat Server Demo (Streamlit App)
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=${STREAMLIT_BIN} run ${APP_DIR}/chat_server_demo/app/app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --server.baseUrlPath=/app
Restart=always
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=${APP_DIR}/${VENV_DIR}/bin:/usr/bin:/bin"
Environment="CHAT_SERVER_DEMO_AZURE_SQL_SERVER=${SQL_SERVER}"
Environment="CHAT_SERVER_DEMO_DB_NAME=${DB_NAME}"
Environment="CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME=${DB_PASS_SECRET}"
Environment="CHAT_SERVER_DEMO_APP_USER_SECRET_NAME=${APP_USER_SECRET}"
Environment="AZURE_KEY_VAULT_URL=https://${VAULT_NAME}.vault.azure.net"
Environment="CHAT_SERVER_DEMO_HOST=https://${DOMAIN}/api/"
Environment="CHAT_SERVER_DEMO_API_KEY=${API_KEY_SECRET_NAME}"
User=${USER}

[Install]
WantedBy=multi-user.target
EOF

# Envs to .bashrc
echo export CHAT_SERVER_DEMO_AZURE_SQL_SERVER=$SQL_SERVER >> ~/.bashrc
echo export CHAT_SERVER_DEMO_DB_NAME=$DB_NAME >> ~/.bashrc
echo export CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME=$DB_PASS_SECRET >> ~/.bashrc
echo export CHAT_SERVER_DEMO_APP_USER_SECRET_NAME=$APP_USER_SECRET >> ~/.bashrc
echo export AZURE_KEY_VAULT_URL=https://$VAULT_NAME.vault.azure.net >> ~/.bashrc
echo export CHAT_SERVER_DEMO_HOST=https://$DOMAIN/api/ >> ~/.bashrc
echo export CHAT_SERVER_DEMO_API_KEY=$API_KEY_SECRET_NAME >> ~/.bashrc
source ~/.bashrc

sudo systemctl daemon-reload
sudo systemctl enable chat_server_demo_app.service
sudo systemctl restart chat_server_demo_app.service

# -------------------------------
# Nginx app.conf
# -------------------------------
msg "🔧 Writing nginx /app/ location config…"
sudo mkdir -p /etc/nginx/locations

APP_LOC=/etc/nginx/locations/app.conf
sudo tee "$APP_LOC" > /dev/null <<EOF
location /app/ {
    proxy_pass http://127.0.0.1:8501/app/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-Port \$server_port;
    proxy_redirect off;
}
EOF

sudo nginx -t && sudo systemctl reload nginx

msg "✅ App installed. Visit: https://${DOMAIN}/app/"
echo "Service logs: sudo journalctl -u chat_server_demo_app -f"
