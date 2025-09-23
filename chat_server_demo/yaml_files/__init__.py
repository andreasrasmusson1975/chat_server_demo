"""
# yaml_files Package

## Introduction

The `yaml_files` package provides centralized configuration management for the chat server demo application through YAML-based data storage and loading utilities. This package serves as the configuration backbone, housing SQL schema definitions and database setup scripts in a structured, maintainable format.

## Core Components

### yaml_loading.py
A utility module that provides safe YAML file loading functionality with automatic path resolution. The module contains a single function `load_yaml()` that handles file path resolution relative to the project structure and uses PyYAML's safe loading mechanism to prevent code execution vulnerabilities.

### sql.yaml
A comprehensive YAML configuration file containing all SQL DDL (Data Definition Language) statements for the chat server database. The file is organized into two main sections:
- **db_creation_and_deletion**: Database, schema, and table creation statements
- **stored_procedures**: Complete stored procedure definitions for all database operations

## Features

- **Safe YAML Loading**: Uses `yaml.safe_load()` to prevent arbitrary code execution
- **Automatic Path Resolution**: Resolves file paths relative to the project root directory
- **Centralized SQL Management**: All database schema and procedure definitions in one location
- **Modular Configuration**: Separates database setup from stored procedures for better organization
- **Type Safety**: Properly typed function signatures with return type annotations

## Technical Architecture

The package follows a simple but effective architecture pattern:

```
yaml_files/
├── __init__.py          # Package initialization and documentation
├── yaml_loading.py      # YAML file loading utilities
└── sql.yaml            # SQL schema and procedure definitions
```

The `yaml_loading.py` module uses Python's `pathlib` for cross-platform path handling and resolves all file paths relative to the package location. This ensures consistent behavior regardless of where the application is executed from.

The `sql.yaml` file uses a hierarchical structure that mirrors the logical organization of database components:
- Database and schema creation at the top level
- Table definitions organized by functional area
- Stored procedures grouped by their purpose (user management, session handling, logging)

## Usage

### Loading YAML Configuration Files

```python
from chat_server_demo.yaml_files.yaml_loading import load_yaml

# Load the SQL configuration
sql_config = load_yaml("sql.yaml")

# Access specific SQL statements
create_db_sql = sql_config["sql"]["db_creation_and_deletion"]["create_db"]
user_procedures = sql_config["sql"]["stored_procedures"]
```

### Accessing SQL Statements

```python
# Get database creation statements
sql_config = load_yaml("sql.yaml")
db_section = sql_config["sql"]["db_creation_and_deletion"]

# Create database
create_db_statement = db_section["create_db"]
create_schema_statement = db_section["create_schema_chatlogs"]

# Get stored procedure definitions
procedures = sql_config["sql"]["stored_procedures"]
insert_user_proc = procedures["create_stored_procedure_insert_new_user"]
```

### Using in Database Setup Scripts

```python
from chat_server_demo.yaml_files.yaml_loading import load_yaml

def create_database():
    sql_config = load_yaml("sql.yaml")
    db_commands = sql_config["sql"]["db_creation_and_deletion"]
    
    # Execute database creation commands
    cursor.execute(db_commands["drop_db_if_exists"])
    cursor.execute(db_commands["create_db"])
    cursor.execute(db_commands["create_schema_chatlogs"])
    # ... continue with other setup commands

def create_stored_procedures():
    sql_config = load_yaml("sql.yaml")
    procedures = sql_config["sql"]["stored_procedures"]
    
    # Create all stored procedures
    for proc_name, proc_sql in procedures.items():
        cursor.execute(proc_sql)
```

### Error Handling

```python
from pathlib import Path
import yaml

try:
    config = load_yaml("sql.yaml")
except FileNotFoundError:
    print("Configuration file not found")
except yaml.YAMLError as e:
    print(f"Error parsing YAML file: {e}")
```
"""