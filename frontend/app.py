import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure Streamlit page
st.set_page_config(
    page_title="Development Portal Q&A",
    page_icon="🤖",
    layout="wide"
)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    
    .user-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    
    .bot-message {
        background-color: #f0f8e8;
        border-left-color: #2ca02c;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Make API request to backend"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure the backend is running on port 8000.")
        return {"error": "Connection failed"}
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API Error: {e}")
        return {"error": str(e)}
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        return {"error": str(e)}

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """Display a chat message with proper formatting"""
    message_class = "user-message" if is_user else "bot-message"
    icon = "👤" if is_user else "🤖"
    
    with st.container():
        st.markdown(f"""
        <div class="chat-message {message_class}">
            <strong>{icon} {"You" if is_user else "Assistant"}:</strong><br>
            {message.get('content', '')}
        </div>
        """, unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

# Main UI
st.markdown('<h1 class="main-header">🤖 Development Portal Q&A Assistant</h1>', unsafe_allow_html=True)

# Display chat history
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message["type"] == "user":
            display_chat_message({"content": message["content"]}, is_user=True)
        else:
            # Display just the answer from the response
            answer = message["content"].get("answer", "No answer received")
            display_chat_message({"content": answer}, is_user=False)

# Question input
question_input = st.text_input(
    "Ask your question:",
    placeholder="e.g., How does the order management process work?",
    key=f"question_input_{st.session_state.input_counter}"
)

# Ask question button
if st.button("🚀 Ask Question", type="primary"):
    if question_input and question_input.strip():
        # Add user message to chat history
        st.session_state.chat_history.append({
            "type": "user",
            "content": question_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message immediately
        display_chat_message({"content": question_input}, is_user=True)
        
        # Get answer from API
        with st.spinner("🤔 Thinking..."):
            response = make_api_request(
                "/qa/ask",
                method="POST",
                data={
                    "question": question_input,
                    "top_k": 3
                }
            )
            
            print("Frontend received response:", response)  # Debug
            print("Response keys:", response.keys() if isinstance(response, dict) else "Not a dict")

            if isinstance(response, dict) and "error" not in response:
                # Check if we have an answer
                answer = response.get("answer", "")
                
                if answer:
                    # Add bot response to chat history
                    st.session_state.chat_history.append({
                        "type": "bot",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Display answer immediately
                    display_chat_message({"content": answer}, is_user=False)
                else:
                    st.error("❌ No answer received from the system")
            else:
                error_msg = response.get("error", "Unknown error occurred") if isinstance(response, dict) else str(response)
                st.error(f"❌ Error: {error_msg}")
        
        # Clear input by incrementing counter
        st.session_state.input_counter += 1
        st.rerun()
    else:
        st.warning("Please enter a question!")

# Clear chat button
if st.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []
    st.rerun() 