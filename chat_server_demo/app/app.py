
"""
Streamlit-based MPAI Assistant chat application.

This module implements a conversational AI web application using Streamlit that provides
an interactive chat interface with multipass answer improvement capabilities. The application
features user authentication, session management, and multiple response modes including
standard responses, improvement mode with internal critique and revision, and optional
display of intermediate processing steps.

Key Features:
    - User authentication and registration system with admin privileges
    - Persistent session and message storage using database backend
    - Multiple chat response modes:
        * Standard mode: Direct responses without improvement
        * Improvement mode: Internal critique and revision of responses
        * Intermediate display: Shows the AI's thought process during improvement
    - Real-time streaming of AI responses with proper formatting
    - Support for LaTeX mathematical expressions and code blocks
    - Session management with ability to create, switch between, and view chat history

The application integrates with a ConversationClient for AI interactions and uses a database
layer for persistent storage of users, sessions, and messages. All user interactions and
database operations are logged for monitoring and debugging purposes.

Classes:
    None (module contains only functions)

Functions:
    hash_password: Creates SHA256 hash of user passwords
    login: Authenticates users and manages session state
    register: Creates new user accounts
    append_message: Persists messages to database and updates session state
    conversation_history_from_messages: Converts session messages to conversation format
    get_reply_improvement_mode_no_intermediate: Streams improved responses without showing steps
    get_reply_display_intermediate: Streams responses showing improvement process
    get_reply_standard_mode: Streams standard responses without improvement
    main: Main application entry point and Streamlit interface controller

Dependencies:
    - streamlit: Web application framework
    - chat_server_demo.client.client: ConversationClient for AI interactions
    - chat_server_demo.database: Database operations and logging
    - chat_server_demo.helper_functionality: Text processing utilities
    
Author: Andreas Rasmusson
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
from chat_server_demo.database.global_logging import log_this   
import hashlib

# ----------------------------
# Auth helpers
# ----------------------------
def hash_password(password: str) -> str:
    """
    Generate a SHA256 hash of a user password for secure storage and authentication.

    This function creates a cryptographic hash of the provided password using the SHA256
    algorithm. The password is encoded as UTF-8 bytes before hashing, and the resulting
    hash is returned as a hexadecimal string. This implementation provides basic password
    security for the authentication system.

    Parameters
    ----------
    password : str
        The plain-text password to be hashed. Must be a valid string that can be
        encoded as UTF-8.

    Returns
    -------
    str
        A 64-character hexadecimal string representing the SHA256 hash of the input
        password. This hash is deterministic - the same password will always produce
        the same hash value.

    Examples
    --------
    >>> hash_password("mypassword123")
    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'
    
    >>> hash_password("admin")
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'
    
    >>> # Same password always produces the same hash
    >>> hash1 = hash_password("test")
    >>> hash2 = hash_password("test")
    >>> hash1 == hash2
    True
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@log_this
def login(username, password_hash):
    """
    Authenticate a user and establish a session in the Streamlit application.

    This function validates user credentials against the database and, upon successful
    authentication, initializes the user session by setting relevant session state
    variables. The function uses the database validation layer to verify the provided
    username and password hash combination, and automatically logs the authentication
    attempt for security monitoring purposes.

    Parameters
    ----------
    username : str
        The username to authenticate. Must match an existing user account in the
        database exactly (case-sensitive).
    password_hash : str
        The SHA256 hexadecimal hash of the user's password, typically generated
        by the `hash_password` function. Must match the stored password hash
        for the given username.

    Returns
    -------
    bool
        True if authentication was successful and the user session was established,
        False if the credentials were invalid or the user was not found.

    Side Effects
    ------------
    On successful authentication, modifies the Streamlit session state:
        - st.session_state.user_id : int
            Sets the authenticated user's unique database ID
        - st.session_state.username : str
            Sets the authenticated user's username for display purposes

    Notes
    -----
    This function is decorated with @log_this, which automatically logs all
    authentication attempts (both successful and failed) to the application
    database for security auditing and monitoring purposes.

    The function does not perform password hashing - it expects the password
    to already be hashed using the same algorithm as stored in the database.
    Use `hash_password` to convert plain-text passwords before calling this function.

    Session state variables are only modified on successful authentication.
    Failed authentication attempts leave the session state unchanged.

    Raises
    ------
    Exception
        May raise database connection errors or other exceptions from the
        underlying database validation layer. These are typically logged
        and handled by the @log_this decorator.
    """
    uid = db.validate_user(username, password_hash)
    if uid:
        st.session_state.user_id = uid
        st.session_state.username = username
        return True
    return False

@log_this
def register(username, email, password_hash):
    """
    Create a new user account and establish an authenticated session.

    This function registers a new user in the system by creating a database record
    with the provided credentials and immediately establishing an authenticated session
    for the newly created user. The registration process includes automatic session
    initialization and logging for security and auditing purposes.

    Parameters
    ----------
    username : str
        The desired username for the new account. Must be unique across all users
        in the system. The username is case-sensitive and will be used for future
        authentication attempts.
    email : str
        The email address associated with the new account. Used for user identification
        and potential communication. Should be a valid email format, though format
        validation is not enforced at this function level.
    password_hash : str
        The SHA256 hexadecimal hash of the user's chosen password, typically generated
        by the `hash_password` function. The raw password should never be passed to
        this function directly for security reasons.

    Returns
    -------
    int
        The unique user ID (primary key) assigned to the newly created user account
        in the database. This ID is used for all subsequent user operations and
        relationship mappings.

    Side Effects
    ------------
    On successful registration, modifies the Streamlit session state:
        - st.session_state.user_id : int
            Sets to the new user's unique database ID
        - st.session_state.session_id : None
            Explicitly clears any existing session ID to ensure clean state

    Database Effects:
        - Creates a new record in the Login.Users table
        - Assigns a unique user ID via database auto-increment

    Notes
    -----
    This function is decorated with @log_this, which automatically logs all
    registration attempts to the application database for security auditing
    and user management purposes.

    The function assumes the database operation will succeed. Database constraint
    violations (e.g., duplicate username) will raise exceptions that should be
    handled by the calling code.

    After successful registration, the user is automatically logged in and their
    session state is initialized. No separate login call is required.

    The session_id is explicitly set to None to ensure no previous session
    data persists for the newly registered user.

    Raises
    ------
    Exception
        May raise database integrity errors if the username already exists or
        other database constraints are violated. Common scenarios include:
        - Duplicate username (database constraint violation)
        - Database connection errors
        - Invalid data format errors
    """
    uid = db.create_user(username, email, password_hash)
    st.session_state.user_id = uid
    st.session_state.session_id = None
    return uid


# ----------------------------
# Helper functions for getting replies
# ----------------------------

def append_message(role: str, content: str, parent=None):
    """
    Persist a chat message to the database and update the session message history.

    This function handles the dual responsibility of storing a new message in the
    persistent database storage and updating the current session's message list
    in Streamlit session state. It creates a complete message record with proper
    indexing and relationship tracking for conversation threading and history
    management.

    Parameters
    ----------
    role : str
        The role identifier for the message sender. Typically "user" for user
        inputs or "assistant" for AI-generated responses. This categorizes the
        message source for conversation flow and display formatting.
    content : str
        The actual text content of the message. Can contain markdown formatting,
        LaTeX expressions, code blocks, or plain text depending on the message
        type and source.
    parent : int, optional
        The message ID of the parent message in conversation threading scenarios.
        Used for creating response chains and conversation branching. Defaults
        to None for top-level messages that are not replies to specific previous
        messages.

    Returns
    -------
    None
        This function performs database operations and session state updates
        in place without returning values.

    Side Effects
    ------------
    Database Effects:
        - Inserts a new message record into the database via db.insert_message()
        - Associates the message with the current session_id from session state

    Session State Effects:
        - Appends a new message dictionary to st.session_state.messages
        - Updates MessageIndex to reflect the current position in conversation
        - Maintains conversation order and threading information

    Notes
    -----
    The function relies on st.session_state.session_id being properly initialized
    before calling. This session_id links the message to the appropriate conversation
    context in the database.

    The MessageIndex is calculated as the length of the current messages list,
    providing a sequential ordering system for message display and navigation.

    All database operations are handled through the db module, which manages
    connection pooling, error handling, and transaction management automatically.

    Raises
    ------
    Exception
        May raise database connection errors or constraint violations if:
        - session_id is invalid or None
        - Database connection is unavailable
        - Message content violates database constraints
    """
    
    msg_id = db.insert_message(
        st.session_state.session_id, role, content, parent
    )
    st.session_state.messages.append({
        "Role": role,
        "Message": content,
        "ParentMessageId": parent,
        "MessageIndex": len(st.session_state.messages)
    })

def conversation_history_from_messages():
    """
    Convert session messages to conversation history format for AI client interactions.

    This function transforms the Streamlit session message list into the standardized
    conversation history format expected by the ConversationClient. It extracts the
    essential role and content information from each message while discarding
    session-specific metadata, creating a clean conversation thread suitable for
    AI processing and context management.

    Parameters
    ----------
    None
        This function operates on the global Streamlit session state and does not
        require explicit parameters. It accesses st.session_state.messages directly.

    Returns
    -------
    list of dict
        A list of conversation dictionaries, each containing:
        - "role" : str
            The message sender role ("user" or "assistant")
        - "content" : str
            The actual message text content
        
        Returns an empty list if no messages exist in the current session.

    Notes
    -----
    The function performs a data format transformation from the internal session
    message structure (which includes MessageIndex, ParentMessageId, and other
    metadata) to the simplified conversation format used by AI clients.

    The conversion maps the following fields:
    - message["Role"] → conversation["role"]
    - message["Message"] → conversation["content"]

    This standardized format is compatible with most conversational AI APIs and
    enables seamless integration with the ConversationClient for maintaining
    conversation context across multiple interactions.

    The function preserves message order as stored in the session state, which
    typically follows chronological ordering based on MessageIndex.
    
    """
    if "messages" not in st.session_state:
        return []

    return [
        {"role": msg["Role"].lower(), "content": msg["Message"]}
        for msg in sorted(st.session_state.messages, key=lambda m: m["MessageIndex"])
    ]
        

@log_this
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

@log_this
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
    parts = display_text.split("### Revised Answer")
    if len(parts) > 2:
        final_answer = parts[2].split("### Comments", 1)[0]
    else:
        final_answer = display_text
    append_message("assistant", fix_latex_delimiters(ensure_fenced_code(final_answer)[0])[0])

@log_this
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
    Launch and orchestrate the complete Streamlit-based MPAI Assistant chat application.

    This function serves as the primary entry point and controller for the entire chat
    application, managing all aspects of the user interface, authentication, session
    management, and conversational AI interactions. It implements a comprehensive
    web-based chat interface with multipass answer improvement capabilities, user
    authentication, persistent storage, and real-time streaming responses.

    The function orchestrates multiple subsystems including user authentication,
    session management, chat history display, conversation client integration,
    and response generation with optional improvement modes. It provides both
    administrative and user-level functionality within a single cohesive interface.

    Parameters
    ----------
    None
        This function operates as a Streamlit application entry point and does not
        require explicit parameters. All state management is handled through
        Streamlit's session state system.

    Returns
    -------
    None
        This function runs indefinitely as a Streamlit web application, handling
        user interactions through the Streamlit framework's event-driven system.
        The function may return early in authentication failure scenarios.

    Key Functional Areas
    -------------------
    Authentication & User Management:
        - Login form with username/password authentication
        - Bootstrap admin user creation for initial setup
        - Admin-only user registration capabilities
        - Session state management for authenticated users
        - Secure logout with state cleanup

    Session Management:
        - Automatic session creation and selection
        - Session switching between multiple conversations
        - Session naming based on first user prompt
        - Persistent session storage and retrieval

    Chat Interface:
        - Real-time message display with role-based formatting
        - Streaming response generation with live updates
        - Support for LaTeX mathematical expressions and code blocks
        - Conversation history persistence and restoration

    AI Integration:
        - ConversationClient management with per-session instances
        - Multiple response modes (standard, improvement, intermediate display)
        - Context-aware conversation history management
        - Configurable improvement and intermediate step display options

    Side Effects
    ------------
    Streamlit UI Effects:
        - Renders complete web application interface
        - Manages sidebar navigation and controls
        - Updates page title and layout configuration
        - Applies custom CSS styling for enhanced UX

    Database Effects:
        - Creates and manages user accounts and authentication
        - Stores and retrieves conversation sessions and messages
        - Logs user actions and system events
        - Maintains relational data integrity across users and sessions

    Session State Effects:
        - Initializes and maintains user authentication state
        - Manages conversation clients and message history
        - Tracks current session and user preferences
        - Handles state transitions for login/logout operations

    Notes
    -----
    The function implements a complete MVC-like architecture within Streamlit's
    reactive framework, where user interactions trigger automatic re-execution
    of relevant portions of the application logic.

    The application supports both single-user bootstrap scenarios (first admin
    creation) and multi-user environments with proper access control and
    session isolation.

    Response streaming is implemented using the ConversationClient's streaming
    capabilities, providing real-time feedback during potentially lengthy
    AI response generation processes.

    The improvement mode feature enables internal critique and revision of
    responses, offering enhanced quality at the cost of increased response time.
    The intermediate display option provides transparency into the AI's
    improvement process.

    Session naming is automatically generated using the AI client itself,
    creating contextually relevant titles based on the initial user prompt
    in each conversation.

    Error Handling:
        - Authentication failures are handled gracefully with user feedback
        - Database errors are logged and typically handled by the @log_this decorator
        - Session state inconsistencies are resolved through automatic cleanup

    Security Considerations:
        - Passwords are hashed using SHA256 before storage
        - Session state isolation prevents cross-user data leakage
        - Admin privileges are required for user creation beyond bootstrap

    Performance Optimizations:
        - ConversationClient instances are cached per session
        - Message history is loaded only when switching sessions
        - CSS styling is applied once and cached by the browser

    Raises
    ------
    Exception
        May raise various exceptions related to:
        - Database connectivity issues
        - Streamlit framework errors
        - ConversationClient communication failures
        - File system access problems for logging
        
        Most exceptions are handled gracefully by Streamlit's error handling
        system and the application's logging infrastructure.
    """
    # ----------------------------
    # Page setup
    # ----------------------------
    st.sidebar.markdown(
        """
        <div style="text-align: center; margin: 10px 0;">
            <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExOW1ocXdiM2RqMWxxY2U2bDV6MTE4dmE2NW10bnF2OXN0N2Y0MjlyNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/MCd33lAKSLajqWT60m/giphy.gif" 
                 width="120" alt="Matrix Gif">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title("🤖 Welcome to the MPAI assistant!")
    # ----------------------------
    # Login / Register
    # ----------------------------
    
    # ----------------------------
    # Sidebar auth controls
    # ----------------------------
    st.sidebar.header("User Access")

    if "user_id" not in st.session_state:
        # --- Login form ---
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login"):
            if login(username, hash_password(password)):
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

        # --- Bootstrap: allow admin registration if no users exist ---
        if db.count_users() == 0:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Create Admin User")
            new_username = st.sidebar.text_input("Admin username", key="bootstrap_username")
            email = st.sidebar.text_input("Email", key="bootstrap_email")
            new_password = st.sidebar.text_input("Password", type="password", key="bootstrap_password")

            if st.sidebar.button("Register Admin"):
                uid = register(new_username, email, hash_password(new_password))
                db.set_admin(uid)
                st.session_state.user_id = uid
                st.session_state.username = new_username   # <-- fix
                st.sidebar.success("Admin user created. You are now logged in.")
                st.rerun()


        st.info("Please log in using the sidebar to start chatting.")
        return

    else:
        # --- Already logged in ---
        st.sidebar.success(f"Logged in as {st.session_state.username}")

        # Logout
        if st.sidebar.button("Logout"):
            for key in ["user_id", "username", "session_id", "messages", "clients", "selected_session"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # --- Registration form only if admin ---
        if db.is_admin(st.session_state.user_id):  # you'd need to add this helper
            st.sidebar.subheader("Register New User")
            new_username = st.sidebar.text_input("New username", key="register_username")
            email = st.sidebar.text_input("Email", key="register_email")
            new_password = st.sidebar.text_input("New password", type="password", key="register_password")

            if st.sidebar.button("Register User"):
                uid = register(new_username, email, hash_password(new_password))
                if uid:
                    st.sidebar.success("User created.")
    
    sessions = db.list_sessions(st.session_state.user_id)
    if "session_id" not in st.session_state or not st.session_state.session_id:
        if sessions:
            # Default to the most recent session
            st.session_state.session_id = sessions[0]["SessionId"]
            st.session_state.messages = db.list_messages(st.session_state.session_id)
        else:
            # No sessions yet → create one
            new_id = db.create_session(st.session_state.user_id)
            st.session_state.session_id = new_id
            st.session_state.messages = []
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

    st.sidebar.header("Sessions")

    # Button to create new session
    if st.sidebar.button("➕ New session"):
        new_id = db.create_session(st.session_state.user_id)
        st.session_state.session_id = new_id
        st.session_state.messages = []
        st.rerun()
    
    # List all sessions (newest first)
    sessions = db.list_sessions(st.session_state.user_id)
    st.markdown("""
    <style>
    /* Make sidebar buttons fixed width (100%), single-line, with ellipsis */
    div[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    }
    </style>
    """, unsafe_allow_html=True)
    for s in sessions:
        full_label = f"{s['Name']}"
        # Optional: manually shorten to keep things tidy (CSS will still ellipsize if needed)
        max_len = 48
        short_label = (full_label[:max_len - 1] + "…") if len(full_label) > max_len else full_label
        if st.session_state.get("session_id") == s["SessionId"]:
            st.sidebar.markdown(f"**▶ {full_label}**")
        else:
            if st.sidebar.button(
                short_label,
                key=f"session_{s['SessionId']}",
                help=full_label,  # hover tooltip shows the full text
            ):
                st.session_state.session_id = s["SessionId"]
                st.session_state.messages = db.list_messages(s["SessionId"])
                st.rerun()


    
    
    
    if "clients" not in st.session_state:
        st.session_state.clients = {}
    
    if st.session_state.session_id not in st.session_state.clients:
        st.session_state.clients[st.session_state.session_id] = ConversationClient()

    client = st.session_state.clients[st.session_state.session_id]
    client.history = conversation_history_from_messages()
    client.improvement = improvement_mode
    client.intermediate_steps = display_intermediate

    # ----------------------------
    # Display history (sorted)
    # ----------------------------
    for msg in sorted(st.session_state.messages, key=lambda m: m["MessageIndex"]):
        with st.chat_message(msg["Role"]):
            st.markdown(msg["Message"])

    # ----------------------------
    # Input + Reply
    # ----------------------------
    if prompt := st.chat_input("Type your message..."):
        append_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        if len(st.session_state.messages) == 1:
            # First message in this session
            first_prompt = prompt
            # Let the model generate a short name
            name_prompt = f"""
            Summarize this chat request in 3-6 words for use as a session title (output only the summary):\n\n{first_prompt}
            """
            client.improvement = False
            session_name = client.chat_blocking(name_prompt)[:200]  # cap length
            client.improvement = improvement_mode
            db.set_session_name(st.session_state.session_id, session_name)


        with st.chat_message("assistant"):
            if improvement_mode:
                if not display_intermediate:
                    get_reply_improvement_mode_no_intermediate(prompt, client)
                else:
                    get_reply_display_intermediate(prompt, client)
            else:
                get_reply_standard_mode(prompt, client)

        st.rerun()
if __name__ == "__main__":
    main()
