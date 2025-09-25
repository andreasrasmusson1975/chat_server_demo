import pytest
from chat_server_demo.client.client import ConversationClient

def test_chat_blocking_live():
    client = ConversationClient()
    reply = client.chat_blocking("Hello, are you alive?")
    assert isinstance(reply, str)
    assert len(reply) > 0
    # history should include both user + assistant
    assert client.history[-2]["content"] == "Hello, are you alive?"
    assert client.history[-1]["role"] == "assistant"

def test_chat_stream_live():
    client = ConversationClient()
    chunks = list(client.chat_stream("Stream a short reply please."))
    full_reply = "".join(chunks)
    assert isinstance(full_reply, str)
    assert len(full_reply) > 0
    # history updated after stream ends
    assert client.history[-2]["content"] == "Stream a short reply please."
    assert client.history[-1]["content"] == full_reply
