
"""
Application launcher module for the MPAI Assistant chat server demo.

This module provides a simple entry point for launching the Streamlit-based MPAI Assistant
web application. It handles the subprocess execution of the main Streamlit app with proper
environment configuration and path resolution, making it easy to start the chat application
from various execution contexts including package installations, development environments,
and command-line interfaces.

Key Features:
    - Automatic discovery of the main Streamlit application file
    - Proper environment variable inheritance for subprocess execution
    - Cross-platform compatibility for launching web applications
    - Integration with Python package entry points and console scripts
    - Simplified deployment and execution workflow

The launcher abstracts away the complexity of Streamlit application startup, providing
a clean interface for users and deployment systems to launch the MPAI Assistant without
needing to know the internal file structure or Streamlit-specific command syntax.

Classes:
    None (module contains only functions)

Functions:
    run: Launches the Streamlit MPAI Assistant web application

Usage:
    This module is typically used as an entry point through setup.py console scripts
    or can be called directly for development and testing purposes:
    
    >>> from chat_server_demo.app.launcher import run
    >>> run()  # Launches the web application
    
    Or via command line if configured as a console script:
    $ chat-server-demo  # Launches via entry point

Dependencies:
    - streamlit: Web application framework for running the main application
    - subprocess: For launching the Streamlit server as a separate process
    - pathlib: For cross-platform path handling and file discovery
    - os: For environment variable management and system integration

Author: Andreas Rasmusson
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
