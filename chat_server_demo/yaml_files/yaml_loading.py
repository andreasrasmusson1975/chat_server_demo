
"""
YAML Configuration Loading Utilities
====================================

This module provides utility functions for loading and parsing YAML configuration files used by the
chat_server_demo application. It supports safe loading of YAML files for model, system prompt, and server
configuration, resolving file paths relative to the project structure.

Features
--------
- Safe loading of YAML files to Python dictionaries
- Centralized access to model, system prompt, and server configuration
- Path resolution relative to the project root for robust file access

Intended for use by application components that require configuration data from YAML files.

Dependencies
------------
- PyYAML
- pathlib
"""

import yaml
from pathlib import Path

def load_yaml(yaml_file_name: str) -> dict:
    """
    Load and parse a YAML file from the project's 'yaml' directory.

    Resolves the file path relative to the project root, opens the YAML file, and returns its contents as a Python dictionary.
    Uses safe loading to avoid executing arbitrary code in the YAML file.

    Args:
        yaml_file_name (str): The name of the YAML file to load (e.g., 'model_config.yaml').

    Returns:
        dict: The parsed contents of the YAML file as a dictionary.
    """
    path = Path(__file__).parent.parent / "yaml_files" / yaml_file_name
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_chat_server_config() -> dict:
    """
    Load the chat server configuration from the 'server_config.yaml' file.

    This function retrieves server-specific configuration parameters such as host, port, and API key
    from the YAML file located in the project's 'yaml' directory. It is typically used to configure
    the connection settings for a chat server.

    Returns:
        dict: The parsed server configuration as a dictionary.
    """
    return load_yaml("server_config.yaml").get("server", {})