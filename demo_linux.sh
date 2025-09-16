#!/usr/bin/env bash
set -euo pipefail

# Change directory to the location of this script
cd "$(dirname "$0")"

# Activate the Python virtual environment
source env/bin/activate

# Start the main application (must be installed in the venv as a console script)
start_app

# Keep the shell open after the app exits (optional)
# Comment this out if you don’t want it to hang
exec $SHELL
