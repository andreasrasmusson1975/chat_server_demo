"""
# Chat Server Demo

## Introduction

The chat_server_demo package is a Streamlit-based web application that demonstrates conversational AI capabilities with multi-pass answer improvement. It provides a complete chat interface with user authentication, session management, and real-time streaming responses. The application connects to a backend LLM server and includes automatic text processing for code blocks and LaTeX math expressions.

## Core Components

- **app/**: Streamlit web application with user interface and chat functionality
  - `app.py`: Main application with authentication, chat interface, and response streaming
  - `launcher.py`: Entry point script for starting the Streamlit application
- **client/**: API client for communicating with the backend LLM server
  - `client.py`: HTTP client with streaming and blocking request capabilities
- **database/**: Data persistence layer with Azure SQL Database integration
  - Database operations for users, sessions, messages, and application logging
- **helper_functionality/**: Text processing utilities
  - Code fence validation and repair for markdown content
  - LaTeX math delimiter fixing and normalization
- **yaml_files/**: Configuration management
  - SQL schema definitions and database setup scripts

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

**API Layer**: HTTP client with REST API communication, supporting both blocking and streaming requests with automatic authentication.

**Data Layer**: Azure SQL Database with three-schema design (Login, ChatLogs, AppLogs) using stored procedures for all operations.

**Processing Layer**: Text normalization utilities for markdown code fences and LaTeX math expressions, ensuring consistent rendering across different content types.

The system supports horizontal scaling through stateless API communication and centralized database storage.
"""