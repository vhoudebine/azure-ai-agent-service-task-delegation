import streamlit as st
import requests

st.title("AI Chat with Task Delegation")

with st.expander("ℹ️ Disclaimer"):
    st.caption(
        """This demo uses a FastAPI backend to simulate a chat session and track long-running processes.
        You get a new thread ID when the app loads, and up to 20 messages (10 rounds of conversation) are allowed.
        Use the Processes tab to see the status of any long-running tasks.
        """
    )

# FastAPI backend base URL
FASTAPI_BASE_URL = "http://127.0.0.1:8000"

# On first load, get a new thread id from the backend if not already set
if "thread_id" not in st.session_state:
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}/threads")
        response.raise_for_status()
        data = response.json()
        st.session_state.thread_id = data["thread_id"]
        st.session_state.messages = data["messages"]  # Initialize the chat history
    except Exception as e:
        st.error(f"Error creating thread: {e}")

# Limit conversation length to 20 messages (10 rounds)
if "max_messages" not in st.session_state:
    st.session_state.max_messages = 20

# Create two tabs: Chat and Processes
chat_tab, processes_tab = st.tabs(["Chat", "Processes"])

# ---------------------------
# Chat Tab
# ---------------------------
with chat_tab:
    st.header("Chat with AI")
    messages = st.container(height=400, border=False)
    prompt=st.chat_input("Ask me anything...")
    # Display chat history from session state
    for message in st.session_state.messages:
        with messages.chat_message(message["role"]):
            st.markdown(message["content"])
    with messages:
        if len(st.session_state.messages) >= st.session_state.max_messages:
            st.info("The maximum message limit for this session has been reached. Please restart the app for a new conversation.")
        else:
            if prompt:
                # Record the user message in session state and display it
                st.session_state.messages.append({"role": "user", "content": prompt})
                with messages.chat_message("user"):
                    st.markdown(prompt)
                
                # Prepare payload to send to the FastAPI /chat endpoint
                payload = {
                    "thread_id": st.session_state.thread_id,
                    "message": prompt
                }
                
                try:
                    r = requests.post(f"{FASTAPI_BASE_URL}/chat", json=payload)
                    r.raise_for_status()
                    result = r.json()
                    ai_response = result.get("response", "No response from server")
                except Exception as e:
                    ai_response = f"Error: {e}"
                
                # Record and display the AI's response
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                with messages.chat_message("assistant"):
                    st.markdown(ai_response)

# ---------------------------
# Processes Tab
# ---------------------------
with processes_tab:
    st.header("Process Status")
    
    # Button to manually refresh the process list
    if st.button("Refresh Processes"):
        st.rerun()
    
    try:
        proc_resp = requests.get(f"{FASTAPI_BASE_URL}/processes")
        proc_resp.raise_for_status()
        processes = proc_resp.json()
        
        if processes:
            for process in processes:
                st.write(f"**Process ID:** {process['process_id']}  |  **Status:** {process['status']} |  **Message:** {process['message']}")
        else:
            st.write("No processes found.")
    except Exception as e:
        st.error(f"Error retrieving processes: {e}")
