
"""
Launcher for the MPAI Assistant Streamlit Application
====================================================

This module provides an entry point for launching the MPAI Assistant web application using Streamlit.
It locates the main app file (app.py) and starts it as a subprocess, ensuring the correct environment
and working directory are used. Intended to be used as a convenient launcher or as a package entry point.

Usage
-----
Import and call the `run()` function, or configure as a console script entry point in setup.py.

Dependencies
------------
- Python 3.x
- streamlit
- chat_server_demo (internal modules)
"""

import sys
import subprocess
import os
from pathlib import Path

def run():
    """
    Launch the Streamlit web application for the MPAI Assistant.

    This function locates the main Streamlit app file (app.py) within the current package directory
    and starts it as a subprocess using the current Python interpreter. The environment variables
    are inherited from the current process. The function terminates the current process with the exit
    code returned by the Streamlit subprocess.

    Returns
    -------
    None
        This function does not return; it exits the current process with the Streamlit subprocess exit code.

    Notes
    -----
    - Designed to be used as an entry point for launching the Streamlit-based MPAI Assistant UI.
    - Ensures the correct environment and working directory are used for subprocess execution.
    """
    # Get path to the actual Streamlit app file
    app_path = Path(__file__).parent / "app.py"
    env = os.environ.copy()
    sys.exit(subprocess.call(["python", "-m", "streamlit", "run", str(app_path)], env=env))
