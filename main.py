import streamlit as st
import openai
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the OpenAI client with Streamlit secrets
api_key = st.secrets["general"]["OPENAI_API_KEY"]
openai.api_key = api_key

# Enter your Assistant ID here from environment variables
ASSISTANT_ID = st.secrets["general"].get("ASSISTANT_ID")

# Create a ThreadPoolExecutor for async tasks
executor = ThreadPoolExecutor(max_workers=1)

# Define request limit
REQUEST_LIMIT = 10

async def get_response(user_input, stop_event):
    try:
        # Create a chat completion request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can change the model to the one you're using
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        # Extract the assistant's reply
        message = response.choices[0].message['content']
        return message
    except Exception as e:
        return f"Error: {str(e)}"

# Sidebar chatbot
with st.sidebar:
    st.image("photo.jpg", width=100)  # Replace with the correct path to your photo
    st.header("Chatty")
    st.write("Your virtual assistant")
    
    # Initialize session state if not already
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'stop_event' not in st.session_state:
        st.session_state.stop_event = asyncio.Event()
    if 'future' not in st.session_state:
        st.session_state.future = None
    if 'error_message' not in st.session_state:
        st.session_state.error_message = ""
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    if 'request_count' not in st.session_state:
        st.session_state.request_count = 0  # Initialize request count

    # Display chat history
    st.write("**Chat History:**")
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**Chatty:** {msg['content']}")

    # Function to submit the message
    def submit_message():
        user_input = st.session_state.input_text
        if user_input and not st.session_state.generating:
            if st.session_state.request_count >= REQUEST_LIMIT:
                st.session_state.error_message = "Request limit reached. Please contact support if you need more credits."
                return

            st.session_state.generating = True  # Set generating state to True
            st.session_state.error_message = ""  # Clear previous errors

            # Append user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.input_text = ""  # Clear input field

            # Increment the request count
            st.session_state.request_count += 1

            # Run the API call asynchronously
            st.session_state.stop_event.clear()  # Reset stop event
            st.session_state.future = executor.submit(asyncio.run, get_response(user_input, st.session_state.stop_event))
            response = st.session_state.future.result()

            # Append the response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Set generating state to False
            st.session_state.generating = False

    # Text input field for user input
    st.text_input("Type your message here...", key="input_text", value=st.session_state.input_text, on_change=submit_message, placeholder="Type your message...", disabled=st.session_state.generating or st.session_state.request_count >= REQUEST_LIMIT)

    # Display Send button and Stop button based on generating state
    if st.session_state.generating:
        st.button("Stop", key="stop_button", on_click=lambda: st.session_state.stop_event.set(), help="Click to stop the ongoing request")
    else:
        send_button = st.button("Send", key="send_button", on_click=submit_message, help="Click to send your message")
        if send_button:
            submit_message()

    # Show error message if any
    if st.session_state.error_message:
        st.write(f"**Error:** {st.session_state.error_message}")

# Ensure input field remains at the bottom and fixed
st.markdown("""
    <style>
    .css-1p6g1c7 {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: white;
        padding: 10px;
        box-shadow: 0px 1px 5px rgba(0, 0, 0, 0.2);
    }
    .css-1emrehy {
        position: fixed;
        bottom: 10px;
        right: 10px;  /* Changed from left to right */
        z-index: 1000;
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    .css-1emrehy button {
        background-color: #2196F3;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
    }
    .css-1emrehy .stop-button {
        background-color: #F44336;
        color: white;
    }
    .css-1emrehy .stop-button:hover {
        background-color: #D32F2F;
    }
    .css-1emrehy button:disabled {
        background-color: #B0BEC5;
        cursor: not-allowed;
    }
    </style>
    """, unsafe_allow_html=True)
