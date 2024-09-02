import streamlit as st
from openai import OpenAI
import time
from dotenv import load_dotenv
import os
from database import create_connection, create_table, save_message, load_messages, create_chat, get_chats, create_user, verify_user

load_dotenv()

# Initialize OpenAI API key
API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY)

# Database setup
db_file = "./complainer.db"
conn = create_connection(db_file)
create_table(conn)

st.title("Complainer")

# Sidebar with authentication forms
if 'chat_id' not in st.session_state:
    st.session_state.chat_id = None
    
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation' not in st.session_state:
    st.session_state.conversation = []  # Store the entire conversation

if 'system_prompt_added' not in st.session_state:
    st.session_state.system_prompt_added = False  # Track if the system prompt has been added

# Sidebar with authentication forms
if 'username' not in st.session_state:
    auth_mode = st.sidebar.selectbox("Select Mode", ["Sign In", "Sign Up"])
    if auth_mode == "Sign In":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Sign In"):
            if verify_user(conn, username, password):
                st.session_state.username = username
                st.sidebar.success("Signed in as {}".format(username))
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password")
    else:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        if st.sidebar.button("Sign Up"):
            if password == confirm_password:
                if create_user(conn, username, password):
                    st.session_state.username = username
                    st.sidebar.success("Signed up as {}".format(username))
                    st.rerun()
                else:
                    st.sidebar.error("User already exists")
            else:
                st.sidebar.error("Passwords do not match")
else:
    st.sidebar.success("Logged in as {}".format(st.session_state.username))

    def generate_summary_name(messages):
        # Use OpenAI to generate a summarized name
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:luri-inc:81-103-file-datast:9wqTaPqj",
            messages=[{"role": "system", "content": "Generate a concise title or name based on the following conversation. It must strongly be less than 7 words. Also make sure to not use any quotation marks"}] + messages
        )
        return response.choices[0].message.content.strip()

    def save_chat(name=None):
        chats = get_chats(conn, st.session_state.username)
        chat_exists = False

        if name is None:
            # Generate a summarized name using OpenAI
            summary_name = generate_summary_name(st.session_state.conversation[:2])  # Using first 2 messages for summary
            name = summary_name

        for chat in chats:
            if chat[1] == name:
                st.session_state.chat_id = chat[0]
                chat_exists = True
                break
        if not chat_exists:
            chatid = create_chat(conn, st.session_state.username, name, str(st.session_state.messages))
            st.session_state.chat_id = chatid
        for message in st.session_state.messages:
            save_message(conn, st.session_state.chat_id, message["role"], message["message"])

    def load_chat(name):
        chats = get_chats(conn, st.session_state.username)
        for chat in chats:
            if chat[1] == name:
                st.session_state.messages = load_messages(conn, chat[0])
                st.session_state.chat_id = chat[0]
                break

    def get_openai_response():
        messages = st.session_state.conversation

        # Ensure the system prompt is added only at the start of a new conversation
        if not st.session_state.system_prompt_added:
            with open('system_prompt.txt', 'r', encoding='utf-8') as file:
                system_prompt = file.read()
            messages.insert(0, {"role": "system", "content": system_prompt})
            st.session_state.system_prompt_added = True
        
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:luri-inc:81-103-file-datast:9wqTaPqj",
            messages=messages,
            max_tokens=16384
        )
        return response.choices[0].message.content

    with st.sidebar:
        if st.button("Start New Chat"):
            st.session_state.messages = []
            st.session_state.conversation = []
            st.session_state.system_prompt_added = False
        
        chats = get_chats(conn, st.session_state.username)
        for chat in chats:
            if st.button(chat[1], key=f"chat_{chat[0]}"):
                load_chat(chat[1])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    def greetings():
        if not st.session_state.messages:
            st.markdown("""
                <style>
                    .greeting {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 50vh;
                        text-align: center;
                        margin-top: 50px;
                    }
                    .greeting h1 {
                        color: #7E6551;
                    }
                    .greeting h2 {
                        color: #2F4F4F;
                    }
                </style>
                <div class="greeting">
                    <h2>How can I help you today?</h2>
                </div>
            """, unsafe_allow_html=True)

    greetings()

    # Display all the chat messages above the text input area
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["message"])

    # Keep the input area and submit button at the bottom
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

    user_input = st.text_area("Let's Chat!", value=st.session_state.user_input, height=100)

    if st.button("Submit"):
        if user_input.strip():  # Check if input is not empty
            st.session_state.messages.append({"role": "user", "message": user_input})
            st.session_state.conversation.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                response = get_openai_response()
                for char in response:
                    full_response += char
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.001)
                message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "message": full_response})
            st.session_state.conversation.append({"role": "assistant", "content": full_response})
            
            if len(st.session_state.messages) <= 2:
                save_chat()  # Save with a generated name
            else:
                for message in st.session_state.messages:
                    save_message(conn, st.session_state.chat_id, message["role"], message["message"])

            # Clear the text area by resetting session state
            st.session_state.user_input = ""
            st.experimental_rerun()  # This triggers a rerun, and the input box will be empty

    # The text area will be empty here on rerun after submission
