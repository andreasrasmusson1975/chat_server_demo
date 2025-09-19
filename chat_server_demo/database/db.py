"""
db.py
=====

Database helper module for Chat Server Demo.

Provides high-level functions for working with users, sessions, and messages,
wrapping stored procedure calls in Azure SQL DB.

Uses Azure AD token authentication (DefaultAzureCredential) and pyodbc/SQLAlchemy.
"""

import os
import struct
from struct import pack
import pyodbc
from sqlalchemy import create_engine, text
from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
# -------------------------------
# Settings
# -------------------------------
KV_URL = os.getenv("CHAT_SERVER_DEMO_KEYVAULT_URL")
SERVER = os.getenv("CHAT_SERVER_DEMO_AZURE_SQL_SERVER")
DB_NAME = os.getenv("CHAT_SERVER_DEMO_DB_NAME")
DB_USER = os.getenv("CHAT_SERVER_DEMO_DB_USERNAME")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KV_URL, credential=credential)
DB_PASSWORD secret_client.get_secret(os.getenv("CHAT_SERVER_DEMO_DB_PASS_SECRET_NAME")).value


def _get_engine(database=DB_NAME):
    # token = credential.get_token("https://database.windows.net/.default")
    # rawtoken = token.token.encode("utf-16-le")
    # tokenstruct = struct.pack("<I", len(rawtoken)) + rawtoken

    # connection_string = (
    #     f"mssql+pyodbc:///?odbc_connect="
    #     f"Driver={{ODBC Driver 18 for SQL Server}};"
    #     f"Server=tcp:{SERVER},1433;"
    #     f"Database={database};"
    #     f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
    # )

    # return create_engine(
    #     connection_string,
    #     connect_args={"attrs_before": {1256: tokenstruct}},
    # )
    connection_string = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASS}"
        f"@{SERVER}:1433/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes&TrustServerCertificate=yes&Connection+Timeout=30"
    )
    return create_engine(connection_string)


# -------------------------------
# User functions
# -------------------------------
def create_user(username: str, email: str, password_hash: str) -> int:
    """Insert a new user and return their Id."""
    sql = text("EXEC Login.InsertNewUser @Username=:username, @Email=:email, @PasswordHash=:ph")
    with _get_engine().begin() as conn:
        result = conn.execute(sql, {"username": username, "email": email, "ph": password_hash})
        return int(result.scalar())

def validate_user(username: str, password_hash: str) -> int | None:
    """Validate user credentials. Returns user Id or None."""
    sql = text("SELECT Id FROM Login.Users WHERE Username=:u AND PasswordHash=:ph")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"u": username, "ph": password_hash}).fetchone()
        return int(row.Id) if row else None

# -------------------------------
# Session functions
# -------------------------------
def create_session(user_id: int, expires_at=None) -> str:
    """Create a new chat session for a user and return SessionId (GUID string)."""
    sql = text("EXEC ChatLogs.InsertSession @UserId=:uid, @ExpiresAt=:exp")
    with _get_engine().begin() as conn:
        result = conn.execute(sql, {"uid": user_id, "exp": expires_at})
        return str(result.scalar())

def list_sessions(user_id: int) -> list[dict]:
    """List all sessions for a user (most recent first)."""
    sql = text("EXEC ChatLogs.ListSessionsByUser @UserId=:uid")
    with _get_engine().begin() as conn:
        rows = conn.execute(sql, {"uid": user_id}).fetchall()
        return [dict(r._mapping) for r in rows]

def delete_session(session_id: str) -> None:
    """Delete a session and its messages."""
    sql = text("EXEC ChatLogs.DeleteSession @SessionId=:sid")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"sid": session_id})

def set_session_name(session_id: str, name: str) -> None:
    """Update the name of a session."""
    sql = text("UPDATE ChatLogs.Sessions SET Name = :n WHERE SessionId = :sid")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"sid": session_id, "n": name})


def get_session_name(session_id: str) -> str | None:
    """Fetch the name of a session."""
    sql = text("SELECT Name FROM ChatLogs.Sessions WHERE SessionId = :sid")
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
# Registration related (via sprocs)
# -------------------------------

def count_users() -> int:
    """Return total number of users in the system (via sproc)."""
    sql = text("EXEC Login.CountUsers")
    with _get_engine().begin() as conn:
        row = conn.execute(sql).fetchone()
        return int(row.Cnt) if row else 0


def set_admin(user_id: int) -> None:
    """Mark a user as admin (via sproc)."""
    sql = text("EXEC Login.SetAdmin @UserId=:uid")
    with _get_engine().begin() as conn:
        conn.execute(sql, {"uid": user_id})


def is_admin(user_id: int) -> bool:
    """Check whether a user is an admin (via sproc)."""
    sql = text("EXEC Login.IsAdmin @UserId=:uid")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"uid": user_id}).fetchone()
        return bool(row.IsAdmin) if row else False


def get_username(user_id: int) -> str | None:
    """Fetch the username for a given user id (via sproc)."""
    sql = text("EXEC Login.GetUsername @UserId=:uid")
    with _get_engine().begin() as conn:
        row = conn.execute(sql, {"uid": user_id}).fetchone()
        return row.Username if row else None
