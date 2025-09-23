"""
YAML File Loading Module

This module provides functionality for loading YAML files into Python dictionaries.
It is designed to simplify the process of reading and parsing YAML configuration
files used in the MPAI Assistant chat server demo.

Key Features
------------
- Loads YAML files safely using `yaml.safe_load`
- Resolves file paths relative to the `yaml_files` directory
- Provides a single utility function for streamlined YAML file access

Dependencies
------------
- `yaml`: For parsing YAML content
- `pathlib`: For handling file paths in a platform-independent manner

Functions
---------
- `load_yaml`: Loads a YAML file and returns its content as a Python dictionary
Author
------
Andreas Rasmusson
"""

import yaml
from pathlib import Path

def load_yaml(yaml_file_name: str) -> dict:
    """
    Load a YAML file and return its content as a Python dictionary.

    This function simplifies the process of reading and parsing YAML files by
    resolving file paths relative to the `yaml_files` directory and safely
    loading the content using `yaml.safe_load`. It is designed for use in the
    MPAI Assistant chat server demo to handle configuration and data files.

    Parameters
    ----------
    yaml_file_name : str
        The name of the YAML file to load. The file should be located in the
        `yaml_files` directory relative to the project root.

    Returns
    -------
    dict
        A dictionary containing the parsed content of the YAML file. The keys
        and values correspond to the structure defined in the YAML file.

    Raises
    ------
    FileNotFoundError
        If the specified YAML file does not exist in the `yaml_files` directory.
    yaml.YAMLError
        If there is an error parsing the YAML file.
    """
    path = Path(__file__).parent.parent / "yaml_files" / yaml_file_name
    with open(path, "r") as f:
        return yaml.safe_load(f)