
"""
Database creation and initialization module for the MPAI Assistant chat server demo.

This module provides comprehensive database setup functionality for the MPAI Assistant
application, including Azure SQL Database creation, schema initialization, table creation,
user management, and stored procedure deployment. It handles the complete database
infrastructure setup required for the chat application's persistent storage needs.

Key Features:
    - Azure SQL Database creation and configuration with proper authentication
    - Schema and table creation from YAML-based SQL configuration files
    - Application user creation with appropriate permissions and security
    - Stored procedure deployment for optimized database operations
    - Azure Key Vault integration for secure credential management
    - Token-based authentication using Azure CLI or Default Azure credentials
    - Comprehensive error handling and transaction management
    - Idempotent database setup with proper cleanup and recreation capabilities

The module follows infrastructure-as-code principles by defining database schemas
and operations in YAML configuration files, enabling version control, review
processes, and consistent deployment across different environments.

Architecture:
    The script uses a multi-step approach:
    1. Drop existing database if present (clean slate approach)
    2. Create new database with proper configuration
    3. Initialize schemas, tables, and application users
    4. Deploy stored procedures for optimized operations


Classes:
    None (module contains only functions)

Functions:
    to_utf16le: Converts token strings to UTF-16 little-endian bytes for Azure auth
    get_engine: Creates SQLAlchemy engine with Azure SQL authentication
    run_sql: Executes SQL statements with proper transaction and autocommit handling
    main: Orchestrates the complete database setup process

Configuration:
    The module relies on environment variables and Azure Key Vault for configuration:
    - CHAT_SERVER_DEMO_AZURE_SQL_SERVER: Azure SQL Server hostname
    - AZURE_KEY_VAULT_NAME: Name of the Azure Key Vault containing secrets
    - SQL schema definitions stored in yaml_files/sql.yaml

Dependencies:
    - pyodbc: ODBC database connectivity for SQL Server communication
    - sqlalchemy: Database abstraction layer for engine and connection management
    - azure.identity: Azure authentication for managed identity and CLI credentials
    - azure.keyvault.secrets: Secure retrieval of database passwords from Key Vault
    - yaml: Configuration file parsing for SQL schema definitions
    - pathlib: Cross-platform path handling for configuration file discovery

Author: Andreas Rasmusson
"""

import pyodbc
import yaml
import textwrap
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
import struct
from struct import pack
from sqlalchemy import create_engine, text
from azure.identity import AzureCliCredential


# -------------------------------
# Settings
# -------------------------------
SERVER = os.getenv("CHAT_SERVER_DEMO_AZURE_SQL_SERVER")
DB_NAME = "chatserverdemo"
KEYVAULT_NAME = os.getenv("AZURE_KEY_VAULT_NAME")
APP_USER_SECRET_NAME = "chat-app-user-password"  

# -------------------------------
# Azure identity
# -------------------------------
#credential = DefaultAzureCredential()

credential = AzureCliCredential()
token = credential.get_token("https://database.windows.net/.default")



# Fetch app user password from Key Vault
kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net/"
kv_client = SecretClient(vault_url=kv_uri, credential=credential)
APP_USER_PASSWORD = kv_client.get_secret(APP_USER_SECRET_NAME).value

# -------------------------------
# Helpers
# -------------------------------

def get_engine(database="master"):
    """
    Create a SQLAlchemy engine for Azure SQL Database with token-based authentication.

    This function constructs and returns a configured SQLAlchemy engine that connects
    to Azure SQL Database using Azure Active Directory token authentication. It handles
    the complex setup required for secure, token-based connections including proper
    token encoding, connection string formatting, and ODBC driver configuration.

    Parameters
    ----------
    database : str, optional
        The name of the database to connect to. Defaults to "master", which is
        the system database used for administrative operations like creating
        and dropping databases. For application operations, this would typically
        be set to the target application database name.

    Returns
    -------
    sqlalchemy.engine.Engine
        A configured SQLAlchemy engine instance ready for database operations.
        The engine includes proper Azure SQL authentication, encryption settings,
        and connection pooling configuration.

    Notes
    -----
    The function performs several critical setup operations:

    Token Processing:
        - Extracts the access token from the Azure credential
        - Converts the token to UTF-16 little-endian format using struct.pack
        - Creates a token structure with length prefix for ODBC authentication

    Connection Configuration:
        - Uses the ODBC Driver 18 for SQL Server for optimal Azure SQL compatibility
        - Enables encryption and certificate trust for secure communication
        - Sets appropriate connection timeout for Azure cloud latency
        - Configures the server connection on standard port 1433

    Authentication Method:
        - Uses Azure Active Directory token authentication (attribute 1256)
        - Passes the token structure via ODBC connection attributes
        - Eliminates the need for username/password authentication

    The connection string uses the mssql+pyodbc dialect for SQLAlchemy,
    providing full compatibility with Azure SQL Database features and
    optimal performance for cloud database operations.

    Raises
    ------
    Exception
        May raise various exceptions related to:
        - Azure authentication token retrieval failures
        - ODBC driver configuration issues
        - Network connectivity problems to Azure SQL
        - Invalid database names or access permissions
    """
    exptoken = b''.join(pack('<H', ord(c)) for c in token.token)
    tokenstruct = struct.pack('<I', len(exptoken)) + exptoken

    connection_string = (
        f"mssql+pyodbc:///?odbc_connect="
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={database};"
        f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
    )

    return create_engine(
        connection_string,
        connect_args={"attrs_before": {1256: tokenstruct}},
    )



def run_sql(engine, sql: str, autocommit=False):
    """
    Execute SQL statements with proper transaction management and error handling.

    This function provides a robust interface for executing SQL statements against
    Azure SQL Database with configurable transaction behavior. It handles both
    transactional operations (with automatic rollback on failure) and autocommit
    operations (required for certain DDL operations like CREATE DATABASE).

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        A configured SQLAlchemy engine instance for database connectivity.
        This should be created using the get_engine() function to ensure
        proper Azure SQL authentication and configuration.
    sql : str
        The SQL statement or batch of statements to execute. Can include
        DDL operations (CREATE, DROP, ALTER), DML operations (INSERT, UPDATE,
        DELETE), or administrative commands. Multi-statement batches are supported.
    autocommit : bool, optional
        Controls the transaction behavior for SQL execution. Defaults to False.
        - False: Uses explicit transaction with automatic rollback on error
        - True: Uses autocommit mode required for certain DDL operations

    Returns
    -------
    None
        This function performs database operations without returning values.
        Success is indicated by the absence of exceptions.

    Transaction Modes
    ----------------
    Transactional Mode (autocommit=False):
        - Uses engine.begin() for automatic transaction management
        - Provides ACID compliance with automatic rollback on exceptions
        - Suitable for DML operations and most DDL operations
        - Ensures data consistency and integrity

    Autocommit Mode (autocommit=True):
        - Uses explicit autocommit isolation level
        - Required for operations that cannot run within transactions
        - Includes CREATE DATABASE, DROP DATABASE, and some system operations
        - Each statement commits immediately without rollback capability

    Notes
    -----
    The function uses exec_driver_sql() rather than execute() to ensure
    compatibility with complex SQL batches and Azure SQL-specific syntax.
    This method provides direct access to the underlying database driver
    without SQLAlchemy's query compilation layer.

    For autocommit operations, an explicit commit() is called after
    exec_driver_sql() as a defensive measure, though the autocommit
    isolation level should handle this automatically.

    Error Handling:
        - Transactional mode: Automatic rollback on any exception
        - Autocommit mode: No rollback capability; operations are permanent
        - All database errors are propagated to the caller for handling

    Security Considerations:
        - SQL injection protection should be handled at the caller level
        - This function executes SQL directly without parameter binding
        - Intended for trusted SQL from configuration files, not user input

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        Base class for all SQLAlchemy-related exceptions including:
        - Connection errors
        - SQL syntax errors
        - Permission denied errors
        - Database constraint violations

    pyodbc.Error
        ODBC driver-specific errors including:
        - Network connectivity issues
        - Authentication failures
        - Driver configuration problems
    """
    
    if autocommit:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(sql)
            conn.commit()  # explicit commit for good measure
    else:
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)



# -------------------------------
# Main setup
# -------------------------------
def main():
    """
    Orchestrate the complete database setup process for the MPAI Assistant application.

    This function serves as the primary entry point for database infrastructure creation,
    executing a comprehensive setup sequence that includes database creation, schema
    initialization, table creation, user management, and stored procedure deployment.
    It follows a structured, idempotent approach that ensures a clean, fully configured
    database environment for the MPAI Assistant chat application.

    The function implements a multi-phase setup process designed for both initial
    deployment and development environment recreation, with proper error handling
    and progress reporting throughout the setup sequence.

    Parameters
    ----------
    None
        This function operates using module-level configuration variables and
        environment settings established during module initialization.

    Returns
    -------
    None
        This function performs database setup operations and reports progress
        to stdout. Success is indicated by completion without exceptions and
        a final success message.

    Setup Process
    -------------
    Phase 1 - Configuration Loading:
        - Loads SQL schema definitions from YAML configuration files
        - Performs template substitution for sensitive values (passwords)
        - Parses configuration into structured database and procedure tasks

    Phase 2 - Database Cleanup and Creation:
        - Drops existing database if present (clean slate approach)
        - Creates new database with proper configuration
        - Uses autocommit mode required for database-level operations

    Phase 3 - Schema and Table Initialization:
        - Creates application schemas for logical data organization
        - Deploys table structures for users, sessions, messages, and logging
        - Establishes foreign key relationships and constraints
        - Creates application database users with appropriate permissions

    Phase 4 - Stored Procedure Deployment:
        - Installs optimized stored procedures for data operations
        - Provides efficient database access patterns for the application
        - Implements business logic at the database layer for performance

    Configuration Management
    -----------------------
    The function relies on YAML-based configuration files that define:
    - Database schema structures and relationships
    - Stored procedure definitions and logic
    - User creation and permission assignments
    - Template placeholders for secure credential injection

    Template substitution replaces {APP_USER_PASSWORD} placeholders with
    actual passwords retrieved from Azure Key Vault, ensuring sensitive
    credentials are never stored in configuration files.

    Database Operations
    ------------------
    All database operations use appropriate transaction modes:
    - Database creation/deletion: autocommit mode (required)
    - Schema/table creation: transactional mode (rollback on error)
    - Stored procedure creation: transactional mode (atomic deployment)

    Progress Reporting
    -----------------
    The function provides real-time progress updates to stdout:
    - "Dropping database if exists..."
    - "Creating database..."
    - "Creating schemas, tables, app user..."
    - "Creating stored procedures..."
    - "✅ Database setup complete."

    Notes
    -----
    This function is designed to be idempotent - it can be run multiple times
    safely, as it drops and recreates the database each time. This approach
    ensures consistent state.

    The function separates concerns by using dedicated helper functions:
    - get_engine() for database connection management
    - run_sql() for SQL execution with proper transaction handling
    - Azure Key Vault integration for secure credential management

    Error Handling:
        - Configuration file errors halt execution immediately
        - Database connection failures are propagated to the caller
        - SQL execution errors cause transaction rollback where applicable
        - All errors include context for debugging and troubleshooting

    Security Considerations:
        - Passwords are retrieved from Azure Key Vault, not hardcoded
        - Database connections use Azure AD token authentication
        - Application users are created with minimal required permissions
        - All connections use encryption and secure protocols

    Raises
    ------
    FileNotFoundError
        If the required YAML configuration file is not found at the expected
        location (yaml_files/sql.yaml relative to the module).

    yaml.YAMLError
        If the configuration file contains invalid YAML syntax or structure.

    KeyError
        If required configuration sections are missing from the YAML file.

    sqlalchemy.exc.SQLAlchemyError
        For database connection, authentication, or SQL execution failures.

    azure.core.exceptions.ClientAuthenticationError
        If Azure Key Vault authentication fails or required secrets are inaccessible.
    """
    
    # Load YAML
    yaml_file = Path(__file__).parent.parent / "yaml_files" / "sql.yaml"
    with open(yaml_file, "r") as f:
        yaml_text = f.read()

    yaml_text = yaml_text.replace("{APP_USER_PASSWORD}", APP_USER_PASSWORD)
    config = yaml.safe_load(yaml_text)

    db_tasks = config["sql"]["db_creation_and_deletion"]
    sp_tasks = config["sql"]["stored_procedures"]

    # 1. Drop DB if exists
    print("Dropping database if exists...")
    run_sql(get_engine("master"), db_tasks["drop_db_if_exists"], autocommit=True)

    # 2. Create DB
    print("Creating database...")
    run_sql(get_engine("master"), db_tasks["create_db"], autocommit=True)

    # 3. Create schemas, tables, app user
    print("Creating schemas, tables, app user...")
    for key, sql_block in db_tasks.items():
        if key in ("drop_db_if_exists", "create_db"):
            continue
        run_sql(get_engine(DB_NAME), sql_block)

    # 4. Create stored procedures
    print("Creating stored procedures...")
    for _, sql_block in sp_tasks.items():
        run_sql(get_engine(DB_NAME), sql_block)

    print("✅ Database setup complete.")


if __name__ == "__main__":
    main()
