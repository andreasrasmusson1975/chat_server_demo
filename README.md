# Chat Server Demo

## Introduction

The chat_server_demo package is a Streamlit-based web application that demonstrates conversational AI capabilities with multi-pass answer improvement. It provides a complete chat interface with user authentication, session management, and real-time streaming responses. The application connects to a backend LLM server and includes automatic text processing for code blocks and LaTeX math expressions.

## Core Components

- **app/**: Streamlit web application with user interface and chat functionality
  - `app.py`: Main application with authentication, chat interface, and response streaming
  - `launcher.py`: Entry point script for starting the Streamlit application
- **client/**: API client for communicating with the backend LLM server
  - `client.py`: Client with streaming and blocking request capabilities
- **database/**: Data persistence layer with Azure SQL Database integration
  - Database operations for users, sessions, messages, and application logging
- **helper_functionality/**: Text processing utilities
  - Code fence validation and repair for markdown content
  - LaTeX math delimiter fixing and normalization
- **yaml_files/**: Configuration management
  - SQL schema definitions

## Features

### Chat Interface
- Real-time streaming responses with live text updates
- Multi-mode operation: standard, improvement, and intermediate display modes
- Session management with automatic naming and history persistence
- Markdown rendering with code syntax highlighting and LaTeX math support

### User Management
- Secure user authentication with password hashing
- Admin user registration and management capabilities
- Session-based access control and user isolation

### Answer Improvement
- Multi-pass answer improvement with internal critique and revision
- Optional display of intermediate reasoning steps
- Automatic text processing for clean code block and math expression rendering

### Database Integration
- Complete user and session data persistence
- Message history with parent-child relationships
- Application-wide function call logging and error tracking
- Azure Key Vault integration for credential management

## Technical Architecture

The application follows a multi-tier architecture:

**Frontend Layer**: Streamlit web interface with real-time streaming, session state management, and responsive UI components.

**API Layer**: Client with REST API communication, supporting both blocking and streaming requests with automatic authentication.

**Data Layer**: Azure SQL Database with three-schema design (Login, ChatLogs, AppLogs) using stored procedures for all operations.

**Processing Layer**: Text normalization utilities for markdown code fences and LaTeX math expressions, ensuring consistent rendering across different content types.

The system supports horizontal scaling through stateless API communication and centralized database storage.

# Install/Uninstall Package for Chat Server Demo

This package provides automated installation and uninstall scripts for the chat_server_demo application.

## Installation Instructions

The chat_server_demo package includes an installation script (`install.sh`) that automates the complete setup process including system dependencies, Python environment, database configuration, systemd service, and nginx reverse proxy with TLS.

### Prerequisites

- Ubuntu/Debian Linux system with `sudo` access
- Internet connection for downloading dependencies
- Azure account with appropriate permissions for Key Vault access
- Azure sql server instance
- Preferably an Azure vm with a good CUDA GPU 
- Domain name pointing to the machine (for TLS certificate)

### Required Parameters

The installation script requires the following parameters:

- `--sql-server`: Azure SQL Server FQDN (e.g., `myserver.database.windows.net`)
- `--db-name`: Database name (e.g., `chatserverdemo`)
- `--app-user-secret`: Azure Key Vault secret name for app user password
- `--domain`: Domain name for the application (e.g., `myapp.example.com`)

### Optional Parameters

- `--with-db`: Create and initialize the database during installation
- `--fresh`: Remove existing virtual environment before creating a new one
- `--venv DIR`: Specify custom virtual environment directory (default: `env`)

### Basic Installation

```bash
./install.sh --sql-server myserver.database.windows.net \
             --db-name chatserverdemo \
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \
             --domain myapp.example.com
```

### Installation with Database Creation

```bash
./install.sh --sql-server myserver.database.windows.net \
             --db-name chatserverdemo \
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \
             --domain myapp.example.com \
             --with-db
```

### Fresh Installation

To perform a clean installation (removes existing virtual environment):

```bash
./install.sh --sql-server myserver.database.windows.net \
             --db-name chatserverdemo \
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \
             --domain myapp.example.com \
             --fresh
```

### What the Installation Script Does

1. **System Dependencies**: Installs Python 3, build tools, nginx, ODBC drivers, and Azure CLI
2. **Authentication**: Prompts for Azure login if not already authenticated
3. **Python Environment**: Creates and configures a virtual environment with all required packages
4. **Package Installation**: Installs the chat_server_demo package and its dependencies
5. **Database Setup**: Optionally creates and initializes the database (with `--with-db` flag)
6. **System Service**: Creates and enables a systemd service for automatic startup
7. **Web Server**: Configures nginx as a reverse proxy with automatic TLS certificate generation
8. **Security**: Sets up secure HTTPS access using Let's Encrypt certificates

### Post-Installation

After successful installation, you can:

- Check service status: `sudo systemctl status chat_server_demo`
- View logs: `journalctl -u chat_server_demo -f`
- Access the application: `https://yourdomain.com/app`

### Uninstallation

To remove the chat_server_demo installation:

```bash
# Remove service and nginx config only
./uninstall.sh

# Complete removal including virtual environment
./uninstall.sh --purge
```

### Troubleshooting

- Ensure all required parameters are provided
- Verify your Azure credentials are valid
- Check that your domain DNS is properly configured
- Review installation logs for any error messages
- Ensure your system meets all prerequisites

# app Package

## Introduction

The `app` package contains the main web application interface for the MPAI Assistant chat server demo. Built on Streamlit, it provides a complete chat interface with user authentication, session management, and multiple response modes including a unique improvement mode where the AI critiques and refines its own responses in real-time.

## Core Components

### app.py
The main Streamlit application module that implements the complete chat interface. Contains:
- **Authentication system**: User login, registration, and admin bootstrap functionality
- **Session management**: Creation, selection, and navigation between chat sessions
- **Message handling**: Persistence, display, and real-time streaming of AI responses
- **Response modes**: Standard, improvement, and intermediate display modes
- **UI components**: Chat interface, sidebar controls, and session listing

### launcher.py
A utility module providing programmatic application startup functionality. Contains a single `run()` function that launches the Streamlit application as a subprocess with proper environment handling.

### .streamlit/config.toml
Streamlit configuration file that sets the application theme to dark mode for improved user experience.

## Features

- **Multi-user Support**: User registration, authentication, and session isolation
- **Admin Bootstrap**: Automatic admin user creation when no users exist
- **Session Management**: Create, switch between, and automatically name chat sessions
- **Real-time Streaming**: Live display of AI responses as they are generated
- **Improvement Mode**: AI self-critique and response refinement with optional intermediate step display
- **Message Persistence**: All conversations stored in database with full history
- **Code and LaTeX Support**: Automatic formatting of code blocks and mathematical expressions
- **Responsive UI**: Wide layout with collapsible sidebar and session navigation

## Technical Architecture

The package follows a modular architecture pattern:

```
app/
├── __init__.py              # Package initialization and documentation
├── app.py                   # Main Streamlit application
├── launcher.py              # Application launcher utility
└── .streamlit/
    └── config.toml         # Streamlit configuration
```

### Application Flow
1. **Authentication**: Users log in or admin bootstrap creates initial user
2. **Session Setup**: Load existing session or create new one
3. **Message Exchange**: Users send messages, AI responds with streaming
4. **Persistence**: All messages and sessions stored in database
5. **Navigation**: Users can switch between sessions or create new ones

### Response Processing Modes
- **Standard Mode**: Direct AI response streaming without modification
- **Improvement Mode (Hidden)**: AI generates critique and improved response, displays only final version
- **Improvement Mode (Visible)**: AI generates critique and improved response, displays entire process

## Usage
Once installed, everything is ready, so you can just visit https://yourdomain.com/app and start playing.

# client Package

## Introduction

The `client` package provides a Python client interface for interacting with the MPAI Assistant conversational API server. It handles communication, authentication, conversation history management, and supports both blocking and streaming chat interactions with configurable response modes including multi-pass answer improvement.

## Core Components

### client.py
The main client module containing the `ConversationClient` class. This class encapsulates all functionality needed to communicate with the MPAI Assistant backend server, including:
- **HTTP request handling**: Both blocking and streaming requests with proper timeout configuration
- **Authentication management**: API key-based authentication for all requests
- **Conversation history**: Maintenance of chat context across multiple exchanges
- **Error handling**: Handling of network errors and chunked encoding issues
- **Configuration support**: Configurable improvement mode and intermediate step display

## Features

- **Dual Communication Modes**: Blocking requests for simple interactions and streaming for real-time response display
- **Automatic History Management**: Maintains conversation context automatically without manual intervention
- **API Key Authentication**: Secure authentication using environment variable-based API keys
- **Environment Configuration**: Server URL and API key configuration via environment variables
- **Timeout Handling**: Configurable connection and read timeouts for reliable operation
- **Error Recovery**: Graceful handling of chunked encoding errors in streaming mode
- **Response Mode Control**: Toggle between standard and improvement modes with optional intermediate steps

## Technical Architecture

The package follows a client-server architecture pattern:

```
client/
├── __init__.py          # Package initialization and documentation
└── client.py           # ConversationClient implementation
```

### Communication Flow
1. **Initialization**: Client configures server URL, API key, and response modes
2. **Request Formation**: User prompts combined with conversation history and configuration
3. **HTTP Communication**: Authenticated requests sent to FastAPI backend endpoints
4. **Response Processing**: Streaming or blocking response handling with automatic history updates
5. **Error Handling**: Network errors and encoding issues handled gracefully

### Configuration Management
The client uses environment variables for configuration:
- `CHAT_SERVER_HOST`: Base URL of the API server
- `CHAT_SERVER_API_KEY`: Authentication key for API access

No need to set these manually, it is done automatically on installation.

## Usage

### Basic Setup and Configuration

```python
from chat_server_demo.client.client import ConversationClient

# Create a basic client
client = ConversationClient()
```

### Simple Blocking Chat

```python
# Initialize client with default settings
client = ConversationClient()

# Send a simple message and get complete response
response = client.chat_blocking("Hello, how are you?")
print(response)

# Continue conversation (history is maintained automatically)
follow_up = client.chat_blocking("Can you explain quantum computing?")
print(follow_up)
```

### Streaming Chat with Real-time Display

```python
# Create client for streaming responses
client = ConversationClient()

# Stream response chunks as they arrive
print("Assistant: ", end="")
for chunk in client.chat_stream("Explain machine learning in detail"):
    print(chunk, end="", flush=True)
print()  # New line after complete response
```

### Using Improvement Mode

```python
# Enable improvement mode for better responses
client = ConversationClient(
    improvement=True,
    intermediate_steps=False  # Hide intermediate steps
)

# Get improved response (takes longer but higher quality)
result = client.chat_blocking("Give an advanced explanation of special relativity.")
print(result)  # New line after complete response
```

### Displaying Intermediate Steps

```python
# Show the AI's improvement process
client = ConversationClient(
    improvement=True,
    intermediate_steps=True  # Show critique and revision steps
)

# Stream with visible improvement process
for chunk in client.chat_stream("Write a complex algorithm explanation"):
    print(chunk, end="", flush=True)
```

### Managing Conversation History

```python
client = ConversationClient()

# Check current history
print(f"Messages in history: {len(client.history)}")

# Send messages (history updates automatically)
client.chat_blocking("My name is Alice")
client.chat_blocking("What's my name?")  # AI will remember

# Access conversation history
for message in client.history:
    print(f"{message['role']}: {message['content']}")

# Reset conversation if needed
client.history = []
```

### Error Handling and Robustness

```python
import requests
from requests.exceptions import ChunkedEncodingError, Timeout

client = ConversationClient()

try:
    response = client.chat_blocking("Tell me about AI")
    print(response)
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except Timeout:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")

# Streaming with error handling
try:
    for chunk in client.chat_stream("Long complex question"):
        print(chunk, end="")
except ChunkedEncodingError:
    print("Streaming completed (chunked encoding ended)")
```

### Custom Configuration and Advanced Usage

```python
# Different configurations for different use cases
quick_client = ConversationClient(
    improvement=False,
    intermediate_steps=False
)

detailed_client = ConversationClient(
    improvement=True,
    intermediate_steps=True
)

# Use different clients for different conversation types
quick_response = quick_client.chat_blocking("Quick question")
detailed_analysis = detailed_client.chat_blocking("Complex analysis request")

# Dynamic configuration changes
client = ConversationClient()
client.improvement = True  # Enable improvement mid-conversation
client.intermediate_steps = False  # Disable intermediate display
```

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

# Helper Functionality Package

## Introduction

The helper_functionality package provides text processing utilities for handling and normalizing markdown and LaTeX content. It focuses on code fence validation and repair, as well as LaTeX math delimiter fixing for reliable rendering in chat applications and documentation systems.

## Core Components

- **code_fences.py**: Markdown code fence validation, repair, and language detection utilities
- **latex.py**: LaTeX math delimiter fixing and normalization tools

## Features

### Code Fence Management
- Validates markdown code fences (``` and ~~~) for proper opening and closing
- Automatically repairs unclosed or mismatched code blocks
- Heuristic programming language detection based on code content
- Normalizes fence lengths to prevent conflicts with code content
- Handles section boundaries and prevents fence issues across markdown headers

### LaTeX Math Processing
- Repairs unbalanced or mismatched math delimiters ($, $$, \(, \), \[, \])
- Protects code blocks, comments, and verbatim environments from modification
- Distinguishes between math expressions and currency notation
- Converts align environments to aligned for better markdown compatibility
- Provides detailed edit logs for all changes made

## Technical Architecture

The package implements two main processing pipelines:

**Code Fence Pipeline**: Uses regular expressions to identify fence patterns, validates nesting and closure, and applies repairs while preserving content integrity. Language detection uses pattern matching for common syntax features.

**LaTeX Pipeline**: Employs a tokenizer-based approach to track math delimiter state, respects escape sequences and protected regions, and maintains a stack-based system for proper nesting validation.

Both components return detailed change logs for transparency and debugging.

## Usage

### Code Fence Validation and Repair

```python
from chat_server_demo.helper_functionality.code_fences import (
    validate_code_fences, fix_code_fences, ensure_fenced_code, guess_lang
)

# Validate existing code fences
text = """```python
print('hello')
"""  # missing closing fence
is_valid, issues = validate_code_fences(text)
print(is_valid,issues)
# Returns: (False, ["Unclosed code fence started on line 1"])

# Fix code fence issues
fixed_text, changes = fix_code_fences(text)
print(fixed_text,changes)
# Returns normalized text with proper closing fence

# Complete validation and repair workflow
final_text, all_changes = ensure_fenced_code(text, default_lang="python")
print(final_text,all_changes)
# Language detection
code = """def hello():
    print('world')"""
language = guess_lang(code)  # Returns "python"
print(language)
```

### LaTeX Math Delimiter Repair

```python
from chat_server_demo.helper_functionality.latex import (
    LaTeXFixer, fix_latex_delimiters, fix_align_environments
)

# Basic delimiter fixing
text = "This is inline math $x = 2 and display math $$y = 3"  # unbalanced
fixer = LaTeXFixer(close_on_newline=True)
fixed_text, edits = fixer.fix(text)
print(fixed_text,edits)
# Convenience function for complete LaTeX repair
text_with_align = "\begin{align}x &= 1\\y &= 2\end{align}"
repaired, changes = fix_latex_delimiters(text_with_align)
print(repaired,changes)
# Converts to $$\begin{aligned}...\end{aligned}$$

# Align environment normalization only
aligned_text = fix_align_environments(text_with_align)
print(aligned_text)
```

### Working with Edit Records

```python
# Edit records provide detailed change information
fixer = LaTeXFixer()
fixed_text, edits = fixer.fix("This is inline math $x = 2 and display math $$y = 3")

for edit in edits:
    print(f"{edit.kind}: {edit.reason}")
    if edit.kind == "replace":
        print(f"  Changed '{edit.before}' to '{edit.after}' at position {edit.pos}")
    elif edit.kind == "insert":
        print(f"  Inserted '{edit.after}' at position {edit.pos}")
```

### Language Detection Examples

```python
from chat_server_demo.helper_functionality.code_fences import (
    validate_code_fences, fix_code_fences, ensure_fenced_code, guess_lang
)
# Supports multiple languages
print(guess_lang("SELECT * FROM users"))  # Returns "sql"
print(guess_lang("function test() { console.log('hi'); }"))  # Returns "javascript"
print(guess_lang("#!/bin/bash\necho 'hello'"))  # Returns "bash"
print(guess_lang('{"name": "value"}'))  # Returns "json"
print(guess_lang("key: value\nother: data"))  # Returns "yaml"
```

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
print(sql_config["sql"]["db_creation_and_deletion"]["create_db"])
print(sql_config["sql"]["stored_procedures"])
```