"""
MPAI Assistant Streamlit Application
====================================

Streamlit web application for the MPAI Assistant, an interactive multipass
answer improvement chatbot with persistent sessions.

Features
--------
- Real-time streaming of chatbot responses.
- Modes: standard, improvement, with/without intermediate steps.
- Persistent sessions and messages in Azure SQL DB.
- Login/registration system with password hashing.
"""

import streamlit as st
import hashlib
from chat_server_demo.helper_functionality.code_fences import ensure_fenced_code
from chat_server_demo.helper_functionality.latex import fix_latex_delimiters
from chat_server_demo.client.client import ConversationClient
from chat_server_demo.database import db

st.set_page_config(
    page_title="MPAI Assistant",
    page_icon="🤖",
    layout="wide",
)


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
# Message persistence
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
    # refresh to immediately show new message
    st.rerun()


# ----------------------------
# Reply modes
# ----------------------------
def get_reply_improvement_mode_no_intermediate(prompt: str, client: ConversationClient) -> None:
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
                placeholder.markdown(
                    fix_latex_delimiters(ensure_fenced_code(parts[0])[0])[0]
                )
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(parts[0])[0])[0])


def get_reply_display_intermediate(prompt: str, client: ConversationClient) -> None:
    placeholder = st.empty()
    display_text = ""
    for chunk in client.chat_stream(prompt):
        if chunk is None:
            break
        display_text += chunk
        placeholder.markdown(
            fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0]
        )
    parts = display_text.split("### Revised Answer", 1)
    if len(parts) > 1:
        final_answer = parts[1].split("### Comments", 1)[0]
    else:
        final_answer = display_text
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(final_answer)[0])[0])


def get_reply_standard_mode(prompt: str, client: ConversationClient) -> None:
    placeholder = st.empty()
    display_text = ""
    for chunk in client.chat_stream(prompt):
        if chunk is None:
            break
        display_text += chunk
        placeholder.markdown(
            fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0]
        )
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(display_text)[0])[0])


# ----------------------------
# Main
# ----------------------------
def main():
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
                st.rerun()
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
                st.rerun()
        return

    # ----------------------------
    # User options
    # ----------------------------
    st.sidebar.header("Options")
    improvement_mode = st.sidebar.checkbox(
        "Enable Improvement Mode", value=False, key="improvement_mode"
    )
    display_intermediate = st.sidebar.checkbox(
        "Display intermediate steps", value=False, key="display_intermediate"
    )

    # ----------------------------
    # Sessions
    # ----------------------------
    sessions = db.list_sessions(st.session_state.user_id)

    if sessions:
        session_labels = [
            f"Session {i+1} — {s['CreatedAt']:%Y-%m-%d %H:%M}"
            for i, s in enumerate(sessions)
        ]
        session_ids = [s["SessionId"] for s in sessions]

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
            st.session_state.messages = db.list_messages(st.session_state.session_id)
    else:
        # no sessions yet, create the first
        st.session_state.session_id = db.create_session(st.session_state.user_id)
        st.session_state.messages = []
        st.info("Started your first session.")

    # ----------------------------
    # Client
    # ----------------------------
    if "client" not in st.session_state:
        st.session_state.client = ConversationClient()

    st.session_state.client.improvement = improvement_mode
    st.session_state.client.intermediate_steps = display_intermediate
    client = st.session_state.client

    # ----------------------------
    # Display history
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
