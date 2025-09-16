"""
Client for the Conversation API.

- Maintains conversation history locally.
- Calls the FastAPI server for blocking or streaming replies.
- Adds API key authentication.
"""

import requests
from requests.exceptions import ChunkedEncodingError
from typing import List, Dict, Generator
from chat_server_demo.yaml_files.yaml_loading import load_chat_server_config
import os

CONFIG = load_chat_server_config()
base_url = os.getenv(CONFIG.get("host"))
print(base_url)
api_key = os.getenv(CONFIG.get("api_key"))

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
