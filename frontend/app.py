import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import time
import base64

# Configure Streamlit page
st.set_page_config(
    page_title="Development Portal Q&A",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

# Predefined question suggestions
QUESTION_SUGGESTIONS = [
    "How does the order management process work?",
    "What are the authentication requirements?",
    "How do I integrate with the payment system?",
    "What APIs are available for data retrieval?",
    "How is error handling implemented?",
    "What are the database schema requirements?",
    "How do I set up the development environment?"
]

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fafafa;
        margin-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #e8f4fd, #d1e7fd);
        border-left-color: #1f77b4;
        margin-left: 2rem;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f0f8e8, #e8f5e8);
        border-left-color: #2ca02c;
        margin-right: 2rem;
    }
    
    .question-suggestion {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-block;
    }
    
    .question-suggestion:hover {
        background-color: #e9ecef;
        transform: translateY(-1px);
    }
    
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-online { background-color: #28a745; }
    .status-offline { background-color: #dc3545; }
    .status-checking { background-color: #ffc107; animation: pulse 1s infinite; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def check_backend_status() -> bool:
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, retries: int = 3) -> Dict[str, Any]:
    """Make API request to backend with retry mechanism"""
    for attempt in range(retries):
        try:
            url = f"{BACKEND_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            if attempt == retries - 1:
                st.error("❌ Cannot connect to backend API. Make sure the backend is running on port 8000.")
                return {"error": "Connection failed"}
            time.sleep(1)
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                st.error("❌ Request timed out. The backend might be busy.")
                return {"error": "Request timed out"}
            time.sleep(1)
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error: {e}")
            return {"error": str(e)}
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            return {"error": str(e)}
    
    return {"error": "Max retries exceeded"}

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """Display a chat message with proper formatting"""
    message_class = "user-message" if is_user else "bot-message"
    icon = "👤" if is_user else "🤖"
    
    with st.container():
        if is_user:
            content = message.get('content', '')
        else:
            # Support markdown formatting for bot responses
            content = message.get('content', '')
        
        st.markdown(f"""
        <div class="chat-message {message_class}">
            <strong>{icon} {"You" if is_user else "Assistant"}:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)

def export_chat_history() -> str:
    """Export chat history as downloadable text"""
    if not st.session_state.chat_history:
        return ""
    
    export_text = f"Chat History Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    export_text += "=" * 50 + "\n\n"
    
    for message in st.session_state.chat_history:
        timestamp = message.get('timestamp', 'Unknown time')
        if message["type"] == "user":
            export_text += f"[{timestamp}] USER: {message['content']}\n\n"
        else:
            answer = message["content"].get("answer", "No answer received")
            export_text += f"[{timestamp}] ASSISTANT: {answer}\n\n"
    
    return export_text

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

if "backend_status" not in st.session_state:
    st.session_state.backend_status = None

if "last_status_check" not in st.session_state:
    st.session_state.last_status_check = 0

# Sidebar
with st.sidebar:
    st.markdown("## 🛠️ Control Panel")
    
    # Backend status check
    current_time = time.time()
    if current_time - st.session_state.last_status_check > 30:  # Check every 30 seconds
        st.session_state.backend_status = check_backend_status()
        st.session_state.last_status_check = current_time
    
    status_class = "status-online" if st.session_state.backend_status else "status-offline"
    status_text = "Online" if st.session_state.backend_status else "Offline"
    
    st.markdown(f"""
    <div class="sidebar-info">
        <strong>Backend Status:</strong><br>
        <span class="status-indicator {status_class}"></span>{status_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Chat statistics
    total_messages = len(st.session_state.chat_history)
    user_messages = len([m for m in st.session_state.chat_history if m["type"] == "user"])
    
    st.markdown(f"""
    <div class="sidebar-info">
        <strong>Chat Statistics:</strong><br>
        Total Messages: {total_messages}<br>
        Questions Asked: {user_messages}
    </div>
    """, unsafe_allow_html=True)
    
    # Export chat history
    if st.session_state.chat_history:
        if st.button("📥 Export Chat History"):
            export_text = export_chat_history()
            st.download_button(
                label="Download Chat History",
                data=export_text,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Quick settings
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("Results to retrieve", min_value=1, max_value=10, value=3)

# Main UI
st.markdown('<h1 class="main-header">🤖 Development Portal Q&A Assistant</h1>', unsafe_allow_html=True)

# Question suggestions
if not st.session_state.chat_history:
    st.markdown("### 💡 Try asking about:")
    
    cols = st.columns(2)
    for i, suggestion in enumerate(QUESTION_SUGGESTIONS):
        col = cols[i % 2]
        with col:
            if st.button(f"💭 {suggestion}", key=f"suggestion_{i}"):
                st.session_state.input_counter += 1
                # Set the suggestion as the input
                st.rerun()

# Chat container
chat_container = st.container()

with chat_container:
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message["type"] == "user":
                display_chat_message({"content": message["content"]}, is_user=True)
            else:
                # Display just the answer from the response
                answer = message["content"].get("answer", "No answer received")
                display_chat_message({"content": answer}, is_user=False)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("👋 Welcome! Ask a question to get started.")

# Question input
col1, col2 = st.columns([4, 1])

with col1:
    question_input = st.text_input(
        "Ask your question:",
        placeholder="e.g., How does the order management process work?",
        key=f"question_input_{st.session_state.input_counter}"
    )

with col2:
    ask_button = st.button("🚀 Ask", type="primary", use_container_width=True)

# Handle question submission
if ask_button or (question_input and st.session_state.get('enter_pressed')):
    if question_input and question_input.strip():
        # Add user message to chat history
        st.session_state.chat_history.append({
            "type": "user",
            "content": question_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get answer from API
        with st.spinner("🤔 Analyzing your question..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            response = make_api_request(
                "/qa/ask",
                method="POST",
                data={
                    "question": question_input,
                    "top_k": top_k
                }
            )
            
            progress_bar.empty()

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
                    
                    st.success("✅ Question answered!")
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

# JavaScript for Enter key handling
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        e.preventDefault();
        // Trigger button click
        const button = document.querySelector('[data-testid="baseButton-primary"]');
        if (button) button.click();
    }
});
</script>
""", unsafe_allow_html=True) 