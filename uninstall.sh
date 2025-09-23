#!/usr/bin/env bash

# ---------------------------------------------
# Chat Server Demo Uninstallation Script
#
# This script automates the removal of the MPAI Assistant chat server demo.
# It stops and disables the systemd service, removes application files,
# and optionally purges the Python virtual environment.
#
# Usage:
#   ./uninstall.sh --domain HOST [--purge-venv]
#
# Options:
#   --domain HOST              Domain name associated with the application
#   --purge-venv               Remove the Python virtual environment
#   -h, --help                 Display this help message
#
# Notes:
# - Ensure you have appropriate permissions to stop services and remove files.
# - The script assumes the application is installed in the current directory.
# - Use the `--purge-venv` option to completely remove the virtual environment.
#
# Author:
# Andreas Rasmusson
# ---------------------------------------------


set -Eeuo pipefail
IFS=$'\n\t'

PURGE_VENV=0
DOMAIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --purge-venv) PURGE_VENV=1; shift ;;
    --domain) DOMAIN="${2:?Missing domain}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --domain HOST [--purge-venv]"
      exit 0
      ;;
    *) echo "❌ Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -n "$DOMAIN" ]] || { echo "❌ Missing --domain"; exit 1; }

APP_DIR=$(pwd)
VENV_DIR="${APP_DIR}/env"
SERVICE_FILE="/etc/systemd/system/chat_server_demo_app.service"
APP_LOC="/etc/nginx/locations/app.conf"

msg() { echo -e "👉 $*"; }

# -------------------------------
# Stop & disable systemd service
# -------------------------------
if systemctl is-active --quiet chat_server_demo_app.service; then
  msg "Stopping service…"
  sudo systemctl stop chat_server_demo_app.service
fi
if systemctl is-enabled --quiet chat_server_demo_app.service; then
  msg "Disabling service…"
  sudo systemctl disable chat_server_demo_app.service
fi
if [[ -f "$SERVICE_FILE" ]]; then
  msg "Removing systemd unit…"
  sudo rm -f "$SERVICE_FILE"
  sudo systemctl daemon-reload
fi

# -------------------------------
# Remove nginx /app/ location
# -------------------------------
if [[ -f "$APP_LOC" ]]; then
  msg "Removing nginx app.conf…"
  sudo rm -f "$APP_LOC"
  sudo nginx -t && sudo systemctl reload nginx || true
else
  msg "⚠️ No /etc/nginx/locations/app.conf found (already removed?)"
fi

# -------------------------------
# Optionally purge venv
# -------------------------------
if [[ $PURGE_VENV -eq 1 && -d "$VENV_DIR" ]]; then
  msg "Removing venv at $VENV_DIR…"
  rm -rf "$VENV_DIR"
fi

msg "✅ Streamlit app uninstalled."
