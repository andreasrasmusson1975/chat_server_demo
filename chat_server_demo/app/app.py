
"""
MPAI Assistant Streamlit Application
====================================

This module implements the main web application for the MPAI Assistant, an interactive multipass answer improvement chatbot.
It provides a Streamlit-based user interface for chatting with an AI assistant that can critique and improve its own answers
in real time. The application supports multiple response modes, including standard, improvement, and intermediate step display.

Features
--------
- Real-time streaming of chatbot responses with or without answer improvement and critique steps.
- Sidebar options for enabling improvement mode and displaying intermediate steps.
- Automatic formatting of code blocks and LaTeX expressions for enhanced readability.
- Persistent conversation history using Streamlit session state.
- Example prompts and user guidance for effective interaction.

Usage
-----
Run this module as a Streamlit app to launch the MPAI Assistant web interface. Users can interact with the assistant,
toggle improvement features, and view both the final and intermediate responses as desired.

Dependencies
------------
- streamlit
- chat_server_demo (internal modules for client, YAML loading, code/LaTeX formatting)

"""
import streamlit as st
st.set_page_config(
    page_title="MPAI Assistant", 
    page_icon="🤖", 
    layout="wide"
)

import os
import sys
import subprocess
from chat_server_demo.helper_functionality.code_fences import ensure_fenced_code
from chat_server_demo.helper_functionality.latex import fix_latex_delimiters
from chat_server_demo.client.client import ConversationClient
from chat_server_demo.database import db
import hashlib

# ----------------------------
# Auth helpers
# ----------------------------
def hash_password(password: str) -> str:
    """Hash a password using SHA256 (or bcrypt/argon2 in production)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def login(username, password_hash):
    uid = db.validate_user(username, password_hash)
    if uid:
        st.session_state.user_id = uid
        st.session_state.session_id = None  # reset session on login
        return True
    return False

def register(username, email, password_hash):
    uid = db.create_user(username, email, password_hash)
    st.session_state.user_id = uid
    st.session_state.session_id = None
    return uid


# ----------------------------
# Helper functions for getting replies
# ----------------------------

def append_message(role: str, content: str, parent=None):
    """Persist a message to DB and update session_state mirror."""
    msg_id = db.insert_message(
        st.session_state.session_id, role, content, parent
    )
    st.session_state.messages.append({
        "Id": msg_id,
        "role": role,
        "content": content,
        "ParentMessageId": parent,
    })


def get_reply_improvement_mode_no_intermediate(prompt: str, client: ConversationClient) -> None:
    """
    Stream and display an improved chatbot response without showing intermediate steps.

    This function interacts with a conversational AI client to generate a response to the user's prompt.
    It streams the response in real time, parsing and displaying only the final improved answer, omitting
    any intermediate critique or revision steps. The function also ensures proper formatting of code blocks
    and LaTeX expressions in the output. The final assistant message is appended to the Streamlit session state.

    Parameters
    ----------
    prompt : str
        The user's input message to be sent to the conversational AI.
    client : ConversationClient
        An instance of ConversationClient used to stream the chatbot's response.

    Returns
    -------
    None
        This function updates the Streamlit UI and session state in place.

    Notes
    -----
    - The function expects the streamed response to contain sections separated by
      "### Improvements", "### Revised Answer", and "### Comments".
    - Only the content under "### Revised Answer" is displayed to the user.
    - Code blocks and LaTeX delimiters are automatically fixed for proper rendering.
    - Designed for use in a Streamlit application with session state management.
    """
    chunks = []
    placeholder = st.empty()
    display_text = ""
    for chunk in client.chat_stream(prompt):
        if chunk is None:
            break
        display_text += chunk
        parts = display_text.split("### Improvements", 1)
        if len(parts) == 1:
            placeholder.markdown(parts[0])
        else:
            parts = parts[1].split("### Revised Answer")
            if len(parts) > 1:
                parts = parts[1].split("### Comments", 1)
                placeholder.markdown(fix_latex_delimiters(ensure_fenced_code(parts[0])[0])[0])
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(parts[0])[0])[0])

def get_reply_display_intermediate(prompt: str, client: ConversationClient) -> None:
    """
    Stream and display a chatbot response with intermediate steps.

    This function interacts with a conversational AI client to generate a response to the user's prompt.
    It streams the response in real time, displaying both the intermediate critique or revision steps
    and the final improved answer. The function also ensures proper formatting of code blocks and LaTeX
    expressions in the output. The final assistant message is appended to the Streamlit session state.

    Parameters
    ----------
    prompt : str
        The user's input message to be sent to the conversational AI.
    client : ConversationClient
        An instance of ConversationClient used to stream the chatbot's response.

    Returns
    -------
    None
        This function updates the Streamlit UI and session state in place.

    Notes
    -----
    - The function expects the streamed response to contain sections separated by
      "### Improvements", "### Revised Answer", and "### Comments".
    - All content is displayed to the user, including intermediate steps.
    - Code blocks and LaTeX delimiters are automatically fixed for proper rendering.
    - Designed for use in a Streamlit application with session state management.
    """
    chunks = []
    placeholder = st.empty()
    display_text = ""
    for chunk in client.chat_stream(prompt):
        if chunk is None:
            break
        display_text += chunk
        placeholder.markdown(fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0])
    parts = display_text.split("### Revised Answer", 1)
    if len(parts) > 2:
        final_answer = parts[2].split("### Comments", 1)[0]
    else:
        final_answer = display_text
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(final_answer)[0])[0])

def get_reply_standard_mode(prompt: str, client: ConversationClient) -> None:
    """
    Stream and display a standard chatbot response without improvement or intermediate steps.

    This function interacts with a conversational AI client to generate a response to the user's prompt.
    It streams the response in real time, displaying the output as it is received, without any internal
    critique, revision, or improvement steps. The function ensures proper formatting of code blocks and
    LaTeX expressions in the output. The final assistant message is appended to the Streamlit session state.

    Parameters
    ----------
    prompt : str
        The user's input message to be sent to the conversational AI.
    client : ConversationClient
        An instance of ConversationClient used to stream the chatbot's response.

    Returns
    -------
    None
        This function updates the Streamlit UI and session state in place.

    Notes
    -----
    - The function displays the response as a single, uninterrupted message.
    - Code blocks and LaTeX delimiters are automatically fixed for proper rendering.
    - Designed for use in a Streamlit application with session state management.
    """
    display_text = ""
    placeholder = st.empty()
    for chunk in client.chat_stream(prompt):
        if chunk is None:
            break
        display_text += chunk
        placeholder.markdown(fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0])
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0])



def main():
    """
    Launch and manage the Streamlit-based MPAI Assistant chatbot application.
    """

    # ----------------------------
    # Page setup
    # ----------------------------
    st.title("🤖 Welcome to the MPAI assistant!")
    # ----------------------------
    # Login / Register
    # ----------------------------
    if "user_id" not in st.session_state:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login(username, hash_password(password)):
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

        st.markdown("---")
        st.subheader("Register")
        new_username = st.text_input("New username")
        email = st.text_input("Email")
        new_password = st.text_input("New password", type="password")

        if st.button("Register"):
            uid = register(new_username, email, hash_password(new_password))
            if uid:
                st.success("User created, you are now logged in.")
                st.experimental_rerun()

        return
    st.markdown("""
    This is an interactive demo of the `MPAI assistant`, a multipass answer improvement chatbot. 
    You can chat with the assistant and get responses as with any chatbot. If you enable 
    improvement mode, the assistant will critique and improve its answers internally in real time. 
    This can lead to better responses, especially for complex queries. It may take a bit longer to 
    respond though. If you enable displaying of intermediate steps, you will be able to see the internal
    thought process of the assistant as it critiques and improves its answers.
                
    Don't know what to ask? Here are some example prompts to get you started:
    - `Give an advanced exposition of general relativity theory. Don't forget to include the mathematical formulations. Use KaTeX.`
    - `Implement k-means clustering from scratch in Python with NumPy, including initialization, iterative updates, and convergence check. Follow PEP-8 and document extensively with state-of-the-art docstrings and comments where necessary. Every function must have a corresponding pytest.
       After you've written out the code, give, for each function/class, a brief explanation of how said function/class works.`
    - `Give a mathematical definition of a Turing machine. Include an example of a simple Turing machine that recognizes the language of strings with an even number of 0s. Use KaTeX.
       Also, give an implementation of that Turing machine in C.`
    - `Give a twenty year long forecast on how societal attitudes will evolve in Sweden.`
    """)

    # ----------------------------
    # User options
    # ----------------------------
    st.sidebar.header("Options")
    improvement_mode = st.sidebar.checkbox("Enable Improvement Mode", value=False, key="improvement_mode")
    display_intermediate = st.sidebar.checkbox("Display intermediate steps", value=False, key="display_intermediate")

    # ----------------------------
    # Session state
    # ----------------------------
    if "user_id" not in st.session_state:
        st.warning("Please log in to start chatting.")
        return

    # Load sessions for this user
    sessions = db.list_sessions(st.session_state.user_id)
    session_labels = [
        f"Session {i+1} — {s['CreatedAt']:%Y-%m-%d %H:%M}"
        for i, s in enumerate(sessions)
    ]
    session_ids = [s["Id"] for s in sessions]

    # Dropdown to select a session
    selected = st.sidebar.selectbox(
        "Select chat session",
        ["➕ New session"] + session_labels,
        key="session_picker"
    )

    if selected == "➕ New session":
        st.session_state.session_id = db.create_session(st.session_state.user_id)
        st.session_state.messages = []
    else:
        idx = session_labels.index(selected)
        st.session_state.session_id = session_ids[idx]
        if "messages" not in st.session_state:
            st.session_state.messages = db.list_messages(st.session_state.session_id)

    if "client" not in st.session_state:
        st.session_state.client = ConversationClient()

    # Always update
    st.session_state.client.improvement = improvement_mode
    st.session_state.client.intermediate_steps = display_intermediate
    client = st.session_state.client

    # ----------------------------
    # Display history (sorted)
    # ----------------------------
    for msg in sorted(st.session_state.messages, key=lambda m: m["MessageIndex"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ----------------------------
    # Input + Reply
    # ----------------------------
    if prompt := st.chat_input("Type your message..."):
        append_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if improvement_mode:
                if not display_intermediate:
                    get_reply_improvement_mode_no_intermediate(prompt, client)
                else:
                    get_reply_display_intermediate(prompt, client)
            else:
                get_reply_standard_mode(prompt, client)


if __name__ == "__main__":
    main()
