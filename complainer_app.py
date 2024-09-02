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
                st.experimental_rerun()
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
                    st.experimental_rerun()
                else:
                    st.sidebar.error("User already exists")
            else:
                st.sidebar.error("Passwords do not match")
else:
    st.sidebar.success("Logged in as {}".format(st.session_state.username))
    # Function to save the current chat with a name
    def save_chat(name):
        chats = get_chats(conn, st.session_state.username)
        chat_exists = False
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


    # Function to load a previous chat
    def load_chat(name):
        chats = get_chats(conn, st.session_state.username)
        for chat in chats:
            if chat[1] == name:
                st.session_state.messages = load_messages(conn, chat[0])
                st.session_state.chat_id = chat[0]
                break

    # Function to get response from OpenAI model
    def get_openai_response(prompt):
        # Open the file in read mode ('r')
        with open('system_prompt.txt', 'r', encoding='utf-8') as file:
            # Read the contents of the file into a variable
            file_data = file.read()
        system_prompt = file_data
        
        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:luri-inc:81-103-file-datast:9wqTaPqj",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    # Sidebar with buttons to start a new chat and select previous chats
    with st.sidebar:
        if st.button("Start New Chat"):
            st.session_state.messages = []
        
        chats = get_chats(conn, st.session_state.username)
        for chat in chats:
            if st.button(chat[1], key=f"chat_{chat[0]}"):
                load_chat(chat[1])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Add custom CSS to position the greeting text
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

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["message"])

    

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "message": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            response = get_openai_response(prompt)
            for char in response:
                full_response += char
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.001)  # Adjust the speed of the typing effect here
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "message": full_response})
        

        if len(st.session_state.messages) <= 2:
            # Save the chat immediately after the first response
            chat_name = " ".join(prompt.split()[:3])  # Use the first 3 words as the chat name
            save_placeholder = st.empty()
            for i in range(4):
                save_placeholder.markdown(f"Saving chat as '{chat_name}'" + "." * (i % 4))
                time.sleep(0.5)
            save_placeholder.markdown(f"Chat saved as '{chat_name}'")
            time.sleep(2)  # Wait for 2 seconds
            save_placeholder.empty()
            save_chat(chat_name)
        else:
            for message in st.session_state.messages:
                save_message(conn, st.session_state.chat_id, message["role"], message["message"])


