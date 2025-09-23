
"""
Database access layer module for the MPAI Assistant chat server demo.

This module provides a comprehensive data access layer for the MPAI Assistant application,
implementing all database operations through stored procedures for optimal performance,
security, and maintainability. It serves as the primary interface between the application
logic and the Azure SQL Database, handling user authentication, session management,
message storage, and application logging functionality.

Key Features:
    - Stored procedure-based architecture for optimal database performance
    - Azure Key Vault integration for secure credential management
    - Comprehensive user authentication and authorization support
    - Session-based conversation tracking with GUID identifiers
    - Message storage with threading and relationship capabilities
    - Administrative functions for user and system management
    - Application logging infrastructure for monitoring and debugging
    - Transaction management with automatic rollback on errors
    - Type-safe interfaces with proper parameter binding

The module follows a clean separation of concerns with distinct functional areas for
user management, session handling, message operations, and system administration.
All database interactions use parameterized queries through stored procedures,
ensuring protection against SQL injection attacks and optimal query performance.

Architecture:
    The data access layer implements a facade pattern, providing a simplified interface
    to complex database operations while maintaining strong consistency and ACID
    properties. Each functional area is grouped logically with clear naming conventions
    and consistent error handling approaches.

Database Integration:
    The module connects to Azure SQL Database using SQLAlchemy with the pyodbc driver,
    providing robust connection pooling, transaction management, and error handling.
    All operations are designed to be atomic and consistent with proper rollback
    capabilities for data integrity.

Functional Areas:
    User Management:
        - User registration and authentication
        - Password hash validation and storage
        - Administrative privilege management
        - User profile and metadata operations

    Session Management:
        - Chat session creation and lifecycle management
        - Session listing and organization by user
        - Session naming and metadata updates
        - Session deletion with cascade cleanup

    Message Operations:
        - Message insertion with automatic indexing
        - Conversation history retrieval and ordering
        - Message threading and relationship tracking
        - Role-based message categorization

    System Administration:
        - User counting and system statistics
        - Administrative privilege assignment
        - System monitoring and health checks
        - Application logging and audit trails

Classes:
    None (module contains only functions)

Functions:
    User Management:
        create_user: Register new users with credentials
        validate_user: Authenticate existing users
        count_users: Get total user count for system statistics
        set_admin: Grant administrative privileges
        is_admin: Check administrative status
        get_username: Retrieve username by user ID

    Session Management:
        create_session: Create new chat sessions
        list_sessions: Retrieve user's session history
        delete_session: Remove sessions and associated data
        set_session_name: Update session display names
        get_session_name: Retrieve session display names

    Message Operations:
        insert_message: Store new messages with threading
        list_messages: Retrieve conversation history

    System Operations:
        insert_log: Record application events and errors

    Internal Functions:
        _get_engine: Create configured database engine instances

Configuration:
    The module relies on environment variables and Azure Key Vault for configuration:
    - AZURE_KEY_VAULT_URL: URL of the Azure Key Vault containing secrets
    - CHAT_SERVER_DEMO_AZURE_SQL_SERVER: Azure SQL Server hostname
    - CHAT_SERVER_DEMO_DB_NAME: Target database name
    - CHAT_SERVER_DEMO_APP_USER_SECRET_NAME: Key Vault secret name for database user
    - CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME: Key Vault secret name for database password

Dependencies:
    - sqlalchemy: Database abstraction layer and ORM functionality
    - pyodbc: ODBC database connectivity for SQL Server integration
    - azure.identity: Azure authentication for managed identity credentials
    - azure.keyvault.secrets: Secure retrieval of database credentials
    - json: Serialization for complex data types in logging operations

Error Handling:
    All functions use proper transaction management with automatic rollback
    on exceptions. Database errors are propagated to callers with appropriate
    context for debugging and user feedback. Connection failures are handled
    gracefully with proper resource cleanup.

Author: Andreas Rasmusson
"""

import json
import os
import struct
from struct import pack
import pyodbc
from sqlalchemy import create_engine, text
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
# -------------------------------
# Settings
# -------------------------------
KV_URL = os.getenv("AZURE_KEY_VAULT_URL")
SERVER = os.getenv("CHAT_SERVER_DEMO_AZURE_SQL_SERVER")
DB_NAME = os.getenv("CHAT_SERVER_DEMO_DB_NAME")

credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KV_URL, credential=credential)

# Fetch secrets from Key Vault
DB_USER = secret_client.get_secret(
    os.getenv("CHAT_SERVER_DEMO_APP_USER_SECRET_NAME")
).value
DB_PASSWORD = secret_client.get_secret(
    os.getenv("CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME")
).value


def _get_engine(database=DB_NAME):
    """
    Create a configured SQLAlchemy engine for Azure SQL Database connections.

    This internal function constructs a SQLAlchemy engine with appropriate configuration
    for connecting to Azure SQL Database using username/password authentication. It
    handles connection string formatting, security settings, and driver configuration
    to ensure reliable and secure database connectivity for all application operations.

    Parameters
    ----------
    database : str, optional
        The name of the target database to connect to. Defaults to the configured
        application database name (DB_NAME from environment variables). This allows
        the function to be used for connecting to different databases within the
        same server instance.

    Returns
    -------
    sqlalchemy.engine.Engine
        A configured SQLAlchemy engine instance ready for database operations.
        The engine includes connection pooling, timeout settings, and security
        configurations appropriate for Azure SQL Database connections.
    
    Notes
    Error Handling:
        - Connection failures will raise SQLAlchemy exceptions
        - Invalid database names will cause connection errors
        - Authentication failures will be reported through the engine
        - Network issues will be handled by the underlying driver

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database connection issues including:
        - Invalid server names or connection parameters
        - Authentication failures with provided credentials
        - Network connectivity problems to Azure SQL Database
        - Database access permission issues
    """
    
    connection_string = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}"
        f"@{SERVER}:1433/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes&TrustServerCertificate=yes&Connection+Timeout=30"
    )
    return create_engine(connection_string)


# -------------------------------
# User functions
# -------------------------------
def create_user(username: str, email: str, password_hash: str) -> int:
    """
    Register a new user account in the system with secure credential storage.

    This function creates a new user account by invoking the Login.InsertNewUser stored
    procedure, which handles secure user registration with proper validation, constraint
    checking, and atomic transaction management. The function ensures that usernames
    and email addresses are unique within the system and that password hashes are
    stored securely according to application security policies.

    Parameters
    ----------
    username : str
        The unique username for the new account. Must be non-empty and not already
        exist in the system. Username validation and uniqueness constraints are
        enforced at the database level through the stored procedure.
    email : str
        The user's email address for account communication and recovery purposes.
        Must be a valid email format and unique within the system. Email validation
        and uniqueness constraints are enforced at the database level.
    password_hash : str
        The pre-hashed password for the user account. This should be a securely
        hashed password using an appropriate algorithm (e.g., bcrypt, Argon2).
        The function expects the password to already be hashed and salted by the
        calling application before being passed to this function.

    Returns
    -------
    int
        The unique user ID (integer) assigned to the newly created user account.
        This ID serves as the primary key for the user and is used throughout the
        application for user identification and association with other entities
        such as chat sessions and messages.

    Raises
    ------
    sqlalchemy.exc.IntegrityError
        When attempting to create a user with a username or email that already
        exists in the system, violating unique constraints.
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid parameter values or data types
        - Database constraint violations beyond uniqueness
        - Transaction rollback scenarios
    """
    
    sql = text("EXEC Login.InsertNewUser @Username=:username, @Email=:email, @PasswordHash=:ph")
    with _get_engine().begin() as conn:
        result = conn.execute(sql, {"username": username, "email": email, "ph": password_hash})
        return int(result.scalar())

def validate_user(username: str, password_hash: str) -> int | None:
    """
    Authenticate user credentials and return user ID if valid.

    This function validates user authentication by checking the provided username
    and password hash against stored credentials in the database. It uses the
    Login.ValidateUser stored procedure to perform secure credential verification
    with proper timing attack resistance and consistent response patterns regardless
    of whether the user exists or credentials are invalid.

    Parameters
    ----------
    username : str
        The username to authenticate. Must be a non-empty string representing
        an existing user account in the system. The validation is case-sensitive
        and must match exactly with the stored username.
    password_hash : str
        The pre-hashed password to verify against the stored password hash.
        This should be the same hashing algorithm and salt used during user
        registration. The function expects the password to be already hashed
        by the calling application before being passed to this function.

    Returns
    -------
    int or None
        Returns the unique user ID (integer) if the credentials are valid and
        authentication succeeds. Returns None if the username does not exist
        or if the password hash does not match the stored credentials. The
        function maintains consistent timing regardless of failure reason to
        prevent username enumeration attacks.
    """
    sql = text("EXEC Login.ValidateUser @Username=:u, @PasswordHash=:ph")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"u": username, "ph": password_hash}).fetchone()
        return int(row.Id) if row else None

# -------------------------------
# Session functions
# -------------------------------
def create_session(user_id: int, expires_at=None) -> str:
    """
    Create a new chat session for a user and return the unique session identifier.

    This function initiates a new chat conversation session by invoking the
    ChatLogs.InsertSession stored procedure, which generates a unique GUID-based
    session identifier and establishes the session with proper user association,
    timestamp initialization, and optional expiration management. Each session
    serves as a container for organizing related messages and maintaining
    conversation context within the chat application.

    Parameters
    ----------
    user_id : int
        The unique identifier of the user for whom the session is being created.
        Must correspond to an existing user ID in the system. This establishes
        ownership and access control for the session and all associated messages.
    expires_at : datetime or None, optional
        The optional expiration timestamp for the session. If provided, the session
        will be marked as expired after this time. If None (default), the session
        will not have an automatic expiration and will remain active until
        explicitly deleted. The datetime should be timezone-aware or in UTC.

    Returns
    -------
    str
        A unique session identifier as a GUID string (e.g., "550e8400-e29b-41d4-
        a716-446655440000"). This identifier serves as the primary key for the
        session and is used throughout the application for message association,
        session management, and conversation tracking operations.

    Raises
    ------
    sqlalchemy.exc.IntegrityError
        When attempting to create a session for a non-existent user_id,
        violating foreign key constraints.
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid parameter values or data types
        - Database constraint violations
        - Transaction rollback scenarios
    """
    sql = text("EXEC ChatLogs.InsertSession @UserId=:uid, @ExpiresAt=:exp")
    with _get_engine().begin() as conn:
        result = conn.execute(sql, {"uid": user_id, "exp": expires_at})
        return str(result.scalar())

def list_sessions(user_id: int) -> list[dict]:
    """
    Retrieve all chat sessions for a specific user ordered by most recent first.

    This function fetches a comprehensive list of all chat sessions belonging to
    the specified user by invoking the ChatLogs.ListSessionsByUser stored procedure.
    The results are ordered by creation time with the most recent sessions appearing
    first, providing an intuitive chronological view of the user's conversation
    history. Each session entry includes metadata such as session ID, name,
    creation timestamp, and other relevant session properties.

    Parameters
    ----------
    user_id : int
        The unique identifier of the user whose sessions should be retrieved.
        Must correspond to an existing user ID in the system. Only sessions
        owned by this user will be returned, ensuring proper access control
        and data isolation between users.

    Returns
    -------
    list[dict]
        A list of dictionaries, where each dictionary represents a session with
        its associated metadata. Each dictionary contains session information
        such as:
        - SessionId: The unique GUID identifier for the session
        - Name: The display name of the session (if set)
        - CreatedAt: Timestamp when the session was created
        - ExpiresAt: Optional expiration timestamp (if applicable)
        - Other session metadata as defined by the stored procedure
        
        Returns an empty list if the user has no sessions. The list is ordered
        by creation time in descending order (most recent first).

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid user_id parameter values
        - Database query execution errors
        - Transaction management issues
    """
    
    sql = text("EXEC ChatLogs.ListSessionsByUser @UserId=:uid")
    with _get_engine().begin() as conn:
        rows = conn.execute(sql, {"uid": user_id}).fetchall()
        return [dict(r._mapping) for r in rows]

def delete_session(session_id: str) -> None:
    """
    Permanently delete a chat session and all associated messages.

    This function removes a chat session and all related data from the database
    by invoking the ChatLogs.DeleteSession stored procedure. The operation includes
    cascading deletion of all messages, metadata, and other session-related records
    to ensure complete cleanup and maintain database integrity. This is a permanent
    operation that cannot be undone, making it suitable for user-initiated session
    cleanup or administrative data management tasks.

    Parameters
    ----------
    session_id : str
        The unique GUID identifier of the session to delete. Must be a valid
        session ID that exists in the database. The session and all associated
        data will be permanently removed from the system, including:
        - The session record itself
        - All messages within the session
        - Session metadata and properties
        - Any related conversation threading information

    Returns
    -------
    None
        This function does not return any value. Successful execution indicates
        that the session and all associated data have been permanently deleted.
        No confirmation or count of deleted records is provided.

    Raises
    ------
    sqlalchemy.exc.IntegrityError
        When attempting to delete a session that has dependent records
        not handled by cascading deletion rules.
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid session_id parameter (non-existent session)
        - Database constraint violations during deletion
        - Transaction rollback scenarios
    """
    sql = text("EXEC ChatLogs.DeleteSession @SessionId=:sid")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"sid": session_id})

def set_session_name(session_id: str, name: str) -> None:
    """
    Update the display name of an existing chat session.

    This function modifies the user-defined display name for a chat session by
    invoking the ChatLogs.SetSessionName stored procedure. Session names provide
    a human-readable identifier to help users organize and distinguish between
    their different conversation threads. Names can be set or updated at any time
    during the session lifecycle and are displayed in session lists and user
    interfaces to improve conversation management and navigation.

    Parameters
    ----------
    session_id : str
        The unique GUID identifier of the session whose name should be updated.
        Must correspond to an existing session in the database. The session
        must be accessible to the calling user (authorization should be handled
        at the application layer before calling this function).
    name : str
        The new display name to assign to the session. Can be any string value
        including empty strings. Common naming patterns include descriptive
        titles like "Python Help", "Project Planning", or date-based names.
        The name should be meaningful to the user for easy identification.

    Returns
    -------
    None
        This function does not return any value. Successful execution indicates
        that the session name has been updated in the database. The new name
        will be reflected in subsequent session listings and queries.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid session_id parameter (non-existent session)
        - Database query execution errors
        - Transaction management issues
    """
    sql = text("EXEC ChatLogs.SetSessionName @SessionId=:sid, @Name=:n")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"sid": session_id, "n": name})


def get_session_name(session_id: str) -> str | None:
    """
    Retrieve the display name of a chat session.

    This function fetches the user-defined display name for a chat session by
    invoking the ChatLogs.GetSessionName stored procedure. Session names provide
    human-readable identifiers that help users organize and distinguish between
    their different conversation threads. If no custom name has been set for the
    session, the function returns None, indicating the session should be displayed
    as unnamed in user interfaces.

    Parameters
    ----------
    session_id : str
        The unique GUID identifier of the session whose name should be retrieved.
        Must correspond to an existing session in the database. The function will
        return None for non-existent session IDs rather than raising an error.

    Returns
    -------
    str or None
        The display name of the session if one has been set, or None if:
        - The session exists but has no custom name assigned
        - The session ID does not exist in the database
        - The session name was explicitly set to None or empty string
        
        When None is returned, user interfaces should display the session as
        "Unnamed" or use a default naming convention based on creation date
        or other session metadata.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Database query execution errors
        - Transaction management issues
    """
    sql = text("EXEC ChatLogs.GetSessionName @SessionId=:sid")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"sid": session_id}).fetchone()
        return row.Name if row else None



# -------------------------------
# Message functions
# -------------------------------
def insert_message(session_id: str, role: str, message: str, parent_message_id: int = None) -> int:
    """
    Insert a message into the database and return the new message Id.
    The MessageIndex is assigned automatically by the stored procedure.

    Parameters
    ----------
    session_id : str
        The GUID of the chat session.
    role : str
        The role of the sender ("user" or "assistant").
    message : str
        The message content.
    parent_message_id : int, optional
        The Id of the parent message, if this message is a reply.

    Returns
    -------
    int
        The Id of the newly inserted message.
    """
    sql = text(
        "EXEC ChatLogs.InsertMessage "
        "@SessionId=:sid, @Role=:role, @Message=:msg, @ParentMessageId=:pid"
    )
    with _get_engine().begin() as conn:
        result = conn.execute(sql, {
            "sid": session_id,
            "role": role,
            "msg": message,
            "pid": parent_message_id,
        })
        return int(result.scalar())


def list_messages(session_id: str) -> list[dict]:
    """
    List all messages in a session, ordered by MessageIndex.

    Parameters
    ----------
    session_id : str
        The GUID of the chat session.

    Returns
    -------
    list of dict
        Each dict contains:
            - Id (int)
            - SessionId (str, GUID)
            - Role (str)
            - Message (str)
            - LogTime (datetime)
            - MessageIndex (int)
            - ParentMessageId (int or None)
    """
    sql = text("EXEC ChatLogs.ListMessagesBySession @SessionId=:sid")
    with _get_engine().begin() as conn:
        rows = conn.execute(sql, {"sid": session_id}).fetchall()
        return [dict(r._mapping) for r in rows]


# -------------------------------
# Registration related
# -------------------------------

def count_users() -> int:
    """
    Retrieve the total number of registered users in the system.

    This function returns the current count of all user accounts registered in
    the system by invoking the Login.CountUsers stored procedure. This metric
    is commonly used for administrative dashboards, system monitoring, analytics,
    and capacity planning purposes. The count includes all user accounts regardless
    of their status, including both active and inactive accounts, but excludes
    any deleted or soft-deleted user records.

    Returns
    -------
    int
        The total number of user accounts currently registered in the system.
        Returns 0 if no users are registered or if the database query returns
        no results. The count is guaranteed to be non-negative and represents
        the current state of the user table at the time of execution.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Database query execution errors
        - Transaction management issues
        - Stored procedure execution failures
    """
    sql = text("EXEC Login.CountUsers")
    with _get_engine().begin() as conn:
        row = conn.execute(sql).fetchone()
        return int(row.Cnt) if row else 0


def set_admin(user_id: int) -> None:
    """
    Grant administrative privileges to a user account.

    This function elevates a regular user account to administrative status by
    invoking the Login.SetAdmin stored procedure. Administrative privileges
    provide users with enhanced access to system management functions, user
    administration capabilities, and advanced application features.

    Parameters
    ----------
    user_id : int
        The unique identifier of the user account to be granted administrative
        privileges. Must correspond to an existing user ID in the system. The
        user account will be marked as an administrator and gain access to
        administrative functions throughout the application.

    Returns
    -------
    None
        This function does not return any value. Successful execution indicates
        that the user has been granted administrative privileges. The privilege
        change takes effect immediately and will be reflected in subsequent
        authorization checks.
    Raises
    ------
    sqlalchemy.exc.IntegrityError
        When attempting to grant admin privileges to a non-existent user_id,
        violating foreign key constraints.
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Invalid user_id parameter values
        - Database query execution errors
        - Transaction management issues
    """
    sql = text("EXEC Login.SetAdmin @UserId=:uid")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"uid": user_id})


def is_admin(user_id: int) -> bool:
    """
    Check whether a user account has administrative privileges.

    This function verifies if a user has been granted administrative privileges
    by invoking the Login.IsAdmin stored procedure. Administrative status is used
    throughout the application to control access to sensitive operations, system
    management functions, and administrative interfaces. This is a fundamental
    authorization check that should be performed before allowing access to
    privileged functionality.

    Parameters
    ----------
    user_id : int
        The unique identifier of the user account whose administrative status
        should be checked. Must correspond to an existing user ID in the system.
        The function will return False for non-existent user IDs rather than
        raising an error, providing graceful handling of invalid user references.

    Returns
    -------
    bool
        True if the user has administrative privileges, False otherwise.
        Returns False in the following cases:
        - User exists but does not have administrative privileges
        - User ID does not exist in the system
        - Database query returns no results
        - Administrative flag is explicitly set to False

        The boolean result can be directly used in conditional statements
        for authorization decisions throughout the application.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Database query execution errors
        - Transaction management issues
        - Stored procedure execution failures
    """
    sql = text("EXEC Login.IsAdmin @UserId=:uid")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"uid": user_id}).fetchone()
        return bool(row.IsAdmin) if row else False


def get_username(user_id: int) -> str | None:
    """
    Retrieve the username associated with a user ID.

    This function fetches the username for a given user ID by invoking the
    Login.GetUsername stored procedure. Usernames are the human-readable
    identifiers that users employ to log into the system and are displayed
    throughout the application for user identification. This function is
    commonly used for audit logging, user interface display, administrative
    reporting, and any context where a readable user identifier is needed.

    Parameters
    ----------
    user_id : int
        The unique identifier of the user whose username should be retrieved.
        Must be a valid integer corresponding to an existing user account in
        the system. The function will return None for non-existent user IDs
        rather than raising an error, providing graceful handling of invalid
        user references.

    Returns
    -------
    str or None
        The username associated with the provided user ID if the user exists,
        or None if:
        - The user ID does not exist in the system
        - The database query returns no results
        - The user account has been deleted or is in an invalid state
        
        When None is returned, calling code should handle the absence of a
        username appropriately, such as displaying a default placeholder or
        indicating an unknown user in logs and interfaces.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Database query execution errors
        - Transaction management issues
        - Stored procedure execution failures
    """
    sql = text("EXEC Login.GetUsername @UserId=:uid")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"uid": user_id}).fetchone()
        return row.Username if row else None

# -------------------------------
# Application logging
# -------------------------------
def insert_log(level: str, func_name: str, args=None, kwargs=None, result=None, exception=None, user_id=None):
    """
    Record application events, errors, and operational data in the database.

    This function creates persistent log records by invoking the AppLogs.InsertLog
    stored procedure, providing comprehensive application monitoring, debugging,
    and audit trail capabilities. It captures detailed information about function
    calls, including parameters, results, exceptions, and user context, enabling
    effective troubleshooting, performance analysis, and security auditing across
    the entire application lifecycle.

    Parameters
    ----------
    level : str
        The severity level of the log entry. Common values include:
        - "DEBUG": Detailed information for diagnosing problems
        - "INFO": General information about application flow
        - "WARNING": Something unexpected but recoverable occurred
        - "ERROR": A serious problem that prevented function completion
        - "CRITICAL": A very serious error that may cause system failure
        
        The level should follow standard logging conventions and be consistent
        across the application for effective log filtering and analysis.
    func_name : str
        The name of the function or operation being logged. This should be
        descriptive and consistent to enable effective log searching and
        analysis. Typically includes module and function names for context.
    args : list or tuple, optional
        The positional arguments passed to the function being logged. Will be
        JSON-serialized for storage. Useful for reproducing issues and
        understanding function call patterns. Large or sensitive data should
        be excluded or sanitized before logging.
    kwargs : dict, optional
        The keyword arguments passed to the function being logged. Will be
        JSON-serialized for storage. Provides complete parameter context for
        debugging and analysis. Sensitive information should be excluded or
        masked before logging.
    result : any, optional
        The return value or result of the function execution. Will be converted
        to string for storage. Helpful for understanding successful operations
        and analyzing output patterns. Large results should be truncated or
        summarized to avoid excessive log storage.
    exception : Exception or str, optional
        Exception information if an error occurred during function execution.
        Will be converted to string representation including exception type
        and message. Critical for error tracking and debugging failed operations.
    user_id : int, optional
        The unique identifier of the user associated with the logged operation.
        Enables user-specific log filtering, security auditing, and per-user
        troubleshooting. Should be included whenever user context is available.

    Returns
    -------
    None
        This function does not return any value. Successful execution indicates
        that the log record has been permanently stored in the database and is
        available for querying, analysis, and monitoring purposes.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        For various database operation issues including:
        - Connection failures to the database
        - Database query execution errors
        - Transaction management issues
        - Stored procedure execution failures
    """
    sql = text("""
        EXEC AppLogs.InsertLog 
            @Level=:level, 
            @FunctionName=:func, 
            @Args=:args, 
            @Kwargs=:kwargs, 
            @Result=:result, 
            @Exception=:exc, 
            @UserId=:uid
    """)
    with _get_engine().begin() as conn:
        conn.execute(sql, {
            "level": level,
            "func": func_name,
            "args": json.dumps(args, default=str) if args else None,
            "kwargs": json.dumps(kwargs, default=str) if kwargs else None,
            "result": str(result) if result is not None else None,
            "exc": str(exception) if exception else None,
            "uid": user_id,
        })
