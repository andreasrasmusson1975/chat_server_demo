"""
# client Package

## Introduction

The `client` package provides a Python client interface for interacting with the MPAI Assistant conversational API server. It handles HTTP communication, authentication, conversation history management, and supports both blocking and streaming chat interactions with configurable response modes including multi-pass answer improvement.

## Core Components

### client.py
The main client module containing the `ConversationClient` class. This class encapsulates all functionality needed to communicate with the MPAI Assistant backend server, including:
- **HTTP request handling**: Both blocking and streaming requests with proper timeout configuration
- **Authentication management**: API key-based authentication for all requests
- **Conversation history**: Automatic maintenance of chat context across multiple exchanges
- **Error handling**: Robust handling of network errors and chunked encoding issues
- **Configuration support**: Configurable improvement mode and intermediate step display

## Features

- **Dual Communication Modes**: Blocking requests for simple interactions and streaming for real-time response display
- **Automatic History Management**: Maintains conversation context automatically without manual intervention
- **API Key Authentication**: Secure authentication using environment variable-based API keys
- **Environment Configuration**: Server URL and API key configuration via environment variables
- **Timeout Handling**: Configurable connection and read timeouts for reliable operation
- **Error Recovery**: Graceful handling of chunked encoding errors in streaming mode
- **Response Mode Control**: Toggle between standard and improvement modes with optional intermediate steps
- **Type Safety**: Full type annotations for better IDE support and code reliability

## Technical Architecture

The package follows a simple but effective client-server architecture pattern:

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

## Usage

### Basic Setup and Configuration

```python
import os
from chat_server_demo.client.client import ConversationClient

# Set environment variables (typically done in deployment)
os.environ["CHAT_SERVER_HOST"] = "http://localhost:8000"
os.environ["CHAT_SERVER_API_KEY"] = "your-api-key"

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
response = client.chat_blocking("Explain general relativity with mathematical formulations")
print(response)
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
    print("\nStreaming completed (chunked encoding ended)")
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
"""