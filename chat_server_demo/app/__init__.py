"""
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

### Running the Application

```python
from chat_server_demo.app.launcher import run

# Launch the Streamlit application
run()
```

### Using as Entry Point

```bash
# If configured as entry point in setup.py
start_app
```

### Direct Streamlit Launch

```bash
# Navigate to app directory and run directly
streamlit run app.py
```

### Authentication Flow

```python
# Example of authentication functions used internally
from chat_server_demo.app.app import hash_password, login, register

# Hash a password
password_hash = hash_password("user_password")

# Attempt login (returns True/False)
success = login("username", password_hash)

# Register new user (returns user ID)
user_id = register("username", "email@example.com", password_hash)
```

### Session Management

```python
# Example of session operations (internal app logic)
from chat_server_demo.database import db

# Create new session
session_id = db.create_session(user_id)

# List user sessions
sessions = db.list_sessions(user_id)

# Load session messages
messages = db.list_messages(session_id)
```

### Message Handling

```python
# Example of message persistence (internal app logic)
def append_message(role: str, content: str, parent=None):
    # Store in database
    msg_id = db.insert_message(
        st.session_state.session_id, role, content, parent
    )
    # Update session state
    st.session_state.messages.append({
        "Role": role,
        "Message": content,
        "ParentMessageId": parent,
        "MessageIndex": len(st.session_state.messages)
    })
```

### Custom Response Processing

```python
# Example of streaming response with formatting
from chat_server_demo.helper_functionality.code_fences import ensure_fenced_code
from chat_server_demo.helper_functionality.latex import fix_latex_delimiters

def process_response(display_text):
    # Fix code fencing
    fixed_code, _ = ensure_fenced_code(display_text)
    # Fix LaTeX delimiters
    fixed_latex, _ = fix_latex_delimiters(fixed_code)
    return fixed_latex
```

### Configuration Customization

```toml
# .streamlit/config.toml
[theme]
base="dark"

[server]
maxUploadSize=200

[browser]
gatherUsageStats=false
```
"""