
"""
Conversational AI client module for the MPAI Assistant chat server demo.

This module provides a comprehensive client interface for communicating with the MPAI Assistant
FastAPI backend server. It implements both blocking and streaming conversation modes with support
for multipass answer improvement, intermediate step display, and automatic conversation history
management. The client handles authentication, request formatting, response processing, and
error handling for seamless integration with the Streamlit frontend application.

Key Features:
    - Dual interaction modes: blocking requests and real-time streaming responses
    - Automatic conversation history management with context preservation
    - Azure Key Vault integration for secure API key management
    - Configurable multipass answer improvement for enhanced response quality
    - Optional intermediate step streaming for transparency in AI reasoning
    - Robust error handling with network resilience and timeout management
    - RESTful API integration with proper authentication headers
    - Environment-based configuration for flexible deployment scenarios

The client abstracts the complexity of HTTP communication with the backend AI server,
providing a simple Python interface that maintains conversation state and handles
the technical details of API communication, authentication, and response processing.

Architecture:
    The module follows a client-server architecture where this client communicates
    with a separate FastAPI server that hosts the actual AI models and processing
    logic. This separation enables distributed deployment, load balancing, and
    independent scaling of frontend and backend components.

Security:
    API keys are securely retrieved from Azure Key Vault using DefaultAzureCredential,
    ensuring proper authentication without hardcoded secrets. All requests include
    appropriate authentication headers for server-side validation.

Classes:
    ConversationClient: Main client class for AI conversation interactions

Functions:
    None (module contains only class definitions)

Configuration:
    The module relies on environment variables for configuration:
    - CHAT_SERVER_DEMO_HOST: Base URL of the FastAPI backend server
    - AZURE_KEY_VAULT_URL: URL of the Azure Key Vault containing secrets
    - CHAT_SERVER_DEMO_API_KEY: Name of the API key secret in Key Vault

Dependencies:
    - requests: HTTP client for API communication with the backend server
    - azure.identity: Azure authentication for secure credential management
    - azure.keyvault.secrets: Azure Key Vault integration for API key retrieval
    - typing: Type hints for improved code documentation and IDE support

Author: Andreas Rasmusson
"""

import requests
from requests.exceptions import ChunkedEncodingError
from typing import List, Dict, Generator
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

base_url = os.getenv("CHAT_SERVER_DEMO_HOST")
kv_url = os.getenv("AZURE_KEY_VAULT_URL")
api_key_name = os.getenv("CHAT_SERVER_DEMO_API_KEY")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=kv_url, credential=credential)
api_key = secret_client.get_secret(api_key_name).value

class ConversationClient:
    """
    Client for interacting with the MPAI Assistant conversational API server.

    This class manages conversation history, handles API key authentication, and provides methods
    for both blocking and streaming chat interactions with the backend FastAPI server. It supports
    multi-pass answer improvement and intermediate step streaming, configurable via instance attributes.

    Features
    --------
    - Maintains local conversation history for context-aware interactions.
    - Supports both blocking and streaming chat requests.
    - Adds API key authentication to all requests.
    - Configurable for answer improvement and intermediate step display.

    Usage
    -----
    Instantiate the class and use `chat_blocking` or `chat_stream` to interact with the assistant.
    Conversation history is automatically updated after each exchange.

    Attributes
    ----------
    base_url : str
        The base URL of the API server.
    api_key : str
        API key for authentication.
    improvement : bool
        Whether to enable multi-pass answer improvement.
    intermediate_steps : bool
        Whether to enable streaming of intermediate review steps.
    history : List[Dict[str, str]]
        Local conversation history, updated after each exchange.
    """
    
    def __init__(
        self,
        improvement: bool = False,
        intermediate_steps: bool = False
    ):
        """
        Initialize the ConversationClient.

        Args:
            base_url (str): API server URL.
            api_key (str): API key for authentication.
            improvement (bool): Enable/disable multi-pass improvement.
            intermediate_steps (bool): Enable/disable intermediate review streaming.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.improvement = improvement
        self.intermediate_steps = intermediate_steps
        self.history: List[Dict[str, str]] = []

    def chat_blocking(self, prompt: str) -> str:
        """
        Send a blocking chat request.

        Args:
            prompt (str): The user prompt.

        Returns:
            str: The assistant's reply.
        """
        resp = requests.post(
            f"{self.base_url}/chat/blocking",
            headers={"x-api-key": self.api_key,
                     "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "history": self.history,
                "improvement": self.improvement,
                "intermediate_steps": self.intermediate_steps
            },
            timeout=(10,600)
        )
        resp.raise_for_status()
        reply = resp.json()["reply"]

        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def chat_stream(self, prompt: str) -> Generator[str, None, None]:
        """
        Send a streaming chat request.

        Args:
            prompt (str): The user prompt.

        Yields:
            str: Chunks of the assistant's reply.
        """
        reply = ""
        with requests.post(
            f"{self.base_url}/chat/stream",
            headers={"x-api-key": self.api_key,
                     "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "history": self.history,
                "improvement": self.improvement,
                "intermediate_steps": self.intermediate_steps
            },
            stream=True,
            timeout=(10,600)
        ) as resp:
            resp.raise_for_status()
            try:
                for chunk in resp.iter_content(chunk_size=64, decode_unicode=True):
                    if chunk and "[[END]]" not in chunk:
                        reply += chunk
                        yield chunk
            except ChunkedEncodingError:
                pass

        # update history after stream ends
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": reply})
