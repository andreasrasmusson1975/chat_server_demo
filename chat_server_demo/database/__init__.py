"""
# Database Package

## Introduction

The database package provides a complete data access layer for the chat server demo application. It handles user authentication, chat session management, message storage, and application logging using Azure SQL Database with SQLAlchemy ORM and stored procedures.

## Core Components

- **create_db.py**: Database initialization and schema setup utility
- **db.py**: Main database operations module with user, session, and message functions
- **global_logging.py**: Function decorator for automatic database logging

## Features

- User authentication and management with password hashing
- Chat session creation and management with GUID-based session IDs
- Message storage with hierarchical parent-child relationships
- Application-wide function call logging with error tracking
- Azure Key Vault integration for secure credential management
- Azure Active Directory authentication support
- Stored procedure-based database operations for performance and security

## Technical Architecture

The package implements a three-schema database design:
- **Login schema**: User accounts and authentication
- **ChatLogs schema**: Chat sessions and messages
- **AppLogs schema**: Application logging and monitoring

Database connections are managed through SQLAlchemy with Azure SQL Database, supporting both Azure AD token authentication and SQL authentication. All database operations use stored procedures to ensure data integrity and performance.

## Usage

### User Management

```python
from chat_server_demo.database import db

# Create a new user
user_id = db.create_user("username", "user@example.com", "hashed_password")

# Validate user credentials
user_id = db.validate_user("username", "hashed_password")

# Check if user is admin
is_admin = db.is_admin(user_id)
```

### Session Management

```python
# Create a new chat session
session_id = db.create_session(user_id)

# List user's sessions
sessions = db.list_sessions(user_id)

# Set session name
db.set_session_name(session_id, "My Chat Session")

# Delete a session
db.delete_session(session_id)
```

### Message Operations

```python
# Insert a message
message_id = db.insert_message(session_id, "user", "Hello, how are you?")

# Insert a reply message
reply_id = db.insert_message(session_id, "assistant", "I'm doing well, thank you!", parent_message_id=message_id)

# Get all messages in a session
messages = db.list_messages(session_id)
```

### Automatic Logging

```python
from chat_server_demo.database.global_logging import log_this

@log_this
def my_function(param1, param2):
    # Function calls, results, and exceptions are automatically logged
    return param1 + param2
```

### Database Setup

```python
from chat_server_demo.database.create_db import main

# Initialize the database (drops existing and recreates)
main()
```
"""