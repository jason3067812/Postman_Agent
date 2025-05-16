import streamlit as st
import requests
import json
import os
import re
from pathlib import Path
import ast
from PIL import Image

# Page configuration with improved styling
st.set_page_config(
    page_title="Postman Agent",
    page_icon="🤖",
    layout="centered", 
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Overall theme - Modern Dark Theme with Accent Colors */
    :root {
        --primary: #4F94EF;
        --primary-dark: #3A7BC8;
        --accent: #FF9800;
        --accent-dark: #F57C00;
        --bg-dark: #1A1A1F;
        --bg-medium: #23232D;
        --bg-light: #2A2A36;
        --text-light: #F0F0F0;
        --text-dim: #B0B0B0;
        --border-color: rgba(80, 80, 95, 0.3);
        --success: #4CAF50;
        --warning: #FF9800;
        --tool: #FF9800;
        --response: #4CAF50;
        --shadow: rgba(0, 0, 0, 0.2);
    }

    /* Overall theme adjustments */
    .stApp {
        background-color: var(--bg-dark);
        color: var(--text-light);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Improved header styling */
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.7rem;
        color: var(--primary);
        text-align: center;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: var(--text-dim);
        margin-bottom: 2rem;
        text-align: center;
        font-weight: 400;
    }
    
    /* Chat containers with improved styling */
    .chat-container {
        margin-bottom: 1.5rem;
        border-radius: 12px;
        overflow: hidden;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px var(--shadow);
    }
    
    /* Component styling */
    .highlight {
        background-color: rgba(79, 148, 239, 0.1);
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(79, 148, 239, 0.2);
        box-shadow: 0 2px 6px var(--shadow);
    }
    
    /* Tool call styling - improved */
    .tool-container {
        background-color: var(--bg-light);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 1.2rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 6px var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .tool-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px var(--shadow);
    }
    .tool-header {
        background-color: rgba(255, 152, 0, 0.15);
        padding: 0.8rem 1.2rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        border-bottom: 1px solid rgba(255, 152, 0, 0.25);
    }
    .tool-icon {
        margin-right: 0.7rem;
        color: var(--tool);
    }
    .tool-name {
        font-weight: 600;
        color: var(--tool);
        letter-spacing: 0.2px;
    }
    .tool-content {
        padding: 1rem 1.2rem;
        line-height: 1.6;
    }
    .tool-param {
        color: var(--text-light);
        font-weight: 500;
        margin-right: 0.6rem;
    }
    .tool-value {
        color: var(--text-dim);
        font-family: 'SF Mono', 'Roboto Mono', monospace;
        background-color: rgba(80, 80, 95, 0.2);
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    /* Response styling - improved */
    .response-container {
        background-color: var(--bg-light);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 1.2rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 6px var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .response-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px var(--shadow);
    }
    .response-header {
        background-color: rgba(76, 175, 80, 0.15);
        padding: 0.8rem 1.2rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        border-bottom: 1px solid rgba(76, 175, 80, 0.25);
    }
    .response-icon {
        margin-right: 0.7rem;
        color: var(--response);
    }
    .response-content {
        padding: 1rem 1.2rem;
        color: var(--text-light);
        line-height: 1.6;
    }
    
    /* Success message styling - improved */
    .success-container {
        background-color: rgba(76, 175, 80, 0.1);
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid rgba(76, 175, 80, 0.25);
        margin-bottom: 1.2rem;
        display: flex;
        align-items: flex-start;
        box-shadow: 0 2px 6px var(--shadow);
        transition: transform 0.2s ease;
    }
    .success-container:hover {
        transform: translateY(-2px);
    }
    .success-icon {
        color: var(--success);
        margin-right: 0.8rem;
        font-size: 1.2rem;
    }
    
    /* List styling - improved */
    .list-item {
        padding: 0.5rem 0.2rem;
        border-bottom: 1px solid rgba(80, 80, 95, 0.2);
        transition: background-color 0.15s ease;
    }
    .list-item:hover {
        background-color: rgba(79, 148, 239, 0.05);
    }
    .list-item:last-child {
        border-bottom: none;
    }
    
    /* Button styling - significantly improved */
    .stButton button {
        background-color: var(--primary);
        color: white;
        border-radius: 8px !important;
        width: 100%;
        margin-bottom: 0.6rem;
        transition: all 0.3s ease !important;
        border: none !important;
        padding: 0.6rem 1rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px;
        text-transform: none !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
    }
    .stButton button:hover {
        background-color: var(--primary-dark) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }
    .stButton button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* File uploader styling - improved */
    .stFileUploader button {
        background-color: var(--primary) !important;
        color: white !important;
        transition: all 0.3s !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1rem !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
    }
    .stFileUploader button:hover {
        background-color: var(--primary-dark) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }
    .stFileUploader button:active, 
    .stFileUploader button:focus {
        background-color: var(--accent) !important;
        border-color: var(--accent-dark) !important;
        box-shadow: 0 0 0 0.2rem rgba(255, 152, 0, 0.25) !important;
    }
    
    /* Additional selectors for the file uploader button */
    [data-testid="stFileUploadDropzone"] button,
    .st-emotion-cache-7ym5gk button,
    .st-be button,
    .stFileUpload button,
    [data-testid="fileUploadButton"] {
        background-color: var(--primary) !important;
        color: white !important;
        transition: all 0.3s !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stFileUploadDropzone"] button:hover,
    .st-emotion-cache-7ym5gk button:hover,
    .st-be button:hover,
    .stFileUpload button:hover,
    [data-testid="fileUploadButton"]:hover {
        background-color: var(--primary-dark) !important;
        transform: translateY(-2px);
    }
    
    [data-testid="stFileUploadDropzone"] button:active,
    [data-testid="stFileUploadDropzone"] button:focus,
    .st-emotion-cache-7ym5gk button:active,
    .st-emotion-cache-7ym5gk button:focus,
    .st-be button:active,
    .st-be button:focus,
    .stFileUpload button:active,
    .stFileUpload button:focus,
    [data-testid="fileUploadButton"]:active,
    [data-testid="fileUploadButton"]:focus {
        background-color: var(--accent) !important;
        border-color: var(--accent-dark) !important;
        box-shadow: 0 0 0 0.2rem rgba(255, 152, 0, 0.25) !important;
    }
    
    /* Other elements - improved */
    .upload-section {
        background-color: var(--bg-medium);
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 6px var(--shadow);
    }
    .upload-progress {
        margin-top: 0.7rem;
    }
    
    /* Hide Streamlit elements */
    footer {
        visibility: hidden;
    }
    #MainMenu {
        visibility: hidden;
    }
    header {
        visibility: hidden;
    }
    
    /* Chat styling - improved */
    .stChatMessage {
        background-color: var(--bg-medium) !important;
        padding: 1.2rem !important;
        border-radius: 12px !important;
        margin-bottom: 1.2rem !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 2px 8px var(--shadow) !important;
        transition: transform 0.2s ease;
    }
    .stChatMessage:hover {
        transform: translateY(-2px);
    }
    .stChatMessage [data-testid="chatAvatarIcon-user"] {
        background-color: #E91E63 !important;
    }
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background-color: var(--primary) !important;
    }
    
    /* Input styling - improved */
    .stTextInput input {
        background-color: var(--bg-medium) !important;
        color: white !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.8rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }
    
    /* Add focus and hover styles for text input */
    .stTextInput input:focus, .stTextInput input:hover {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
        outline: none !important;
    }
    
    /* Chat input field specific styles */
    .stChatInputField {
        border-color: var(--border-color) !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }
    
    .stChatInputField:focus-within, .stChatInputField:hover {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }
    
    /* Target the chat input container */
    div[data-testid="stChatInput"] > div {
        border-color: var(--border-color) !important;
        border-radius: 10px !important;
    }
    
    div[data-testid="stChatInput"] > div:focus-within, 
    div[data-testid="stChatInput"] > div:hover {
        border-color: var(--accent) !important; 
        box-shadow: 0 0 0 1px var(--accent) !important;
    }
    
    /* Sidebar styling - improved */
    [data-testid="stSidebar"] {
        background-color: var(--bg-medium) !important;
        border-right: 1px solid var(--border-color);
        padding-top: 0.5rem;
    }
    [data-testid="stSidebarNav"] {
        background-color: var(--bg-medium);
    }
    
    /* Section headers - improved */
    .section-header {
        margin-top: 1.8rem;
        margin-bottom: 1rem;
        color: var(--primary);
        font-size: 1.2rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    
    /* File list styling - improved */
    .file-list {
        background-color: var(--bg-light);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 6px var(--shadow);
    }
    .file-item {
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        border-radius: 6px;
        background-color: var(--bg-medium);
        display: flex;
        align-items: center;
        transition: transform 0.2s ease, background-color 0.2s ease;
    }
    .file-item:hover {
        background-color: rgba(79, 148, 239, 0.1);
        transform: translateY(-1px);
    }
    .file-icon {
        margin-right: 0.7rem;
        color: var(--primary);
    }

    /* Info messages */
    .stAlert {
        background-color: var(--bg-light) !important;
        color: var(--text-light) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        padding: 0.8rem 1rem !important;
    }
    
    /* Selectbox styling */
    .stSelectbox div[data-baseweb="select"] {
        background-color: var(--bg-light) !important;
        border-radius: 8px !important;
        border-color: var(--border-color) !important;
        transition: all 0.2s ease;
    }
    
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: var(--primary) !important;
    }
    
    /* Add animation to the page load */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main .block-container {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Custom sidebar title styling */
    .sidebar-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 0.3rem;
        margin-top: 0.5rem;
        text-align: left;
        letter-spacing: -0.5px;
        line-height: 1.2;
        background: linear-gradient(90deg, var(--primary), #6EB5FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Custom horizontal divider */
    .custom-divider {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 0.8rem 0 1.5rem 0;
    }
    
    /* Improve code blocks */
    pre {
        background-color: var(--bg-dark) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        border: 1px solid var(--border-color) !important;
    }
    
    code {
        font-family: 'SF Mono', 'JetBrains Mono', 'Roboto Mono', monospace !important;
        font-size: 0.9em !important;
    }
    
    /* Spinner improvement */
    .stSpinner {
        border-color: var(--primary) !important;
        border-bottom-color: transparent !important;
    }
    
    /* Improve markdown rendering */
    .stMarkdown h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: var(--primary) !important;
        margin-bottom: 1rem !important;
        margin-top: 1.5rem !important;
    }
    
    .stMarkdown h2 {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: var(--text-light) !important;
        margin-bottom: 0.8rem !important;
        margin-top: 1.2rem !important;
    }
    
    .stMarkdown h3, .stMarkdown h4 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: var(--text-light) !important;
    }
    
    .stMarkdown p, .stMarkdown li {
        line-height: 1.6 !important;
    }
    
    .stMarkdown a {
        color: var(--primary) !important;
        text-decoration: none !important;
        border-bottom: 1px dotted var(--primary) !important;
    }
    
    .stMarkdown a:hover {
        color: var(--accent) !important;
        border-bottom: 1px solid var(--accent) !important;
    }
    
    /* Improve bolded text */
    .stMarkdown strong {
        color: var(--primary) !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main header with improved styling
try:
    # Try to load the local image
    image_path = "img/postman.png"
    if os.path.exists(image_path):
        # Use direct HTML/CSS for precise control over layout
        encoded_image = Image.open(image_path)
        # Convert to base64 for inline embedding
        import base64
        from io import BytesIO
        buffered = BytesIO()
        encoded_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Create HTML with inline image and text
        header_html = f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-top: 20px; animation: fadeIn 0.5s ease-out;">
            <img src="data:image/png;base64,{img_str}" style="width: 48px; height: 48px; margin-right: 15px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
            <h1 style="font-size: 2.4rem; margin: 0; color: #4F94EF; font-weight: 700; letter-spacing: -0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">Postman Agent</h1>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    else:
        # Fallback to robot emoji
        st.markdown("<h1 class='main-header'>🤖 Postman Agent</h1>", unsafe_allow_html=True)
except Exception as e:
    # Fallback to robot emoji if any error occurs
    print(f"Error loading image: {str(e)}")
    st.markdown("<h1 class='main-header'>🤖 Postman Agent</h1>", unsafe_allow_html=True)

st.markdown("<p class='sub-header'>Retrieves and processes data from Postman Collections</p>", unsafe_allow_html=True)

# Backend URL
backend_url = "http://localhost:8000/chat/"

# Helper function to extract tool details from raw text
def parse_tool_call(tool_call_text):
    """Extract tool information from the raw text received from the backend."""
    # Check for empty input first - don't default to 'postman_tool' for empty inputs
    if not tool_call_text or not tool_call_text.strip():
        # If empty, try to use the last successful tool call if it's stored in session state
        if 'last_successful_tool' in st.session_state:
            return st.session_state.last_successful_tool
        # Otherwise use a more specific default like 'load_postman_collection' instead of generic 'postman_tool'
        return {
            'name': 'load_postman_collection',
            'args': {},
            'success': True
        }

    # First try to parse as JSON or Python literal
    try:
        # Check if it's a string representation of a list of dictionaries
        if tool_call_text.strip().startswith("[") and "]" in tool_call_text:
            # Try to parse as Python literal (safer than eval)
            tool_calls = ast.literal_eval(tool_call_text)
            
            # If successful and it's a list with at least one tool call
            if isinstance(tool_calls, list) and len(tool_calls) > 0 and isinstance(tool_calls[0], dict):
                tool_call = tool_calls[0]  # Take the first tool call
                name = tool_call.get('name', '')
                args = tool_call.get('args', {})

                final_response = {
                    'name': name,
                    'args': args if isinstance(args, dict) else {},
                    'success': True
                }
                
                # Store the successful tool call for future reference
                st.session_state.last_successful_tool = final_response
                return final_response
            
        print("Successfully parsed tool call text as Python literal")
        
    except Exception as e:
        pass  # Fallback to old regex-based parsing below

    # --- Fallback: legacy regex-based parsing (for old/unknown formats) ---
    # Special check for load_postman_collection which often appears in different formats
    if "load_postman_collection" in tool_call_text.lower() or "load postman collection" in tool_call_text.lower():
        # Try multiple patterns to extract file path
        file_path = ""
        # Check for structured format
        path_match = re.search(r"'file_path':\s*'([^']*)'", tool_call_text)
        if path_match:
            file_path = path_match.group(1)
        else:
            # Try alternate format
            path_match = re.search(r"file_path.*?['\"]([^'\"]+)['\"]", tool_call_text)
            if path_match:
                file_path = path_match.group(1)
            else:
                # Look for anything that resembles a path to a .json file
                path_match = re.search(r"backend/data/[\w._-]+\.json", tool_call_text)
                if path_match:
                    file_path = path_match.group(0)
        
        result = {
            'name': 'load_postman_collection',
            'args': {'file_path': file_path},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    # Check for other specific tools
    elif "list_all_endpoints" in tool_call_text.lower():
        result = {
            'name': 'list_all_endpoints',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "search_endpoints_by_keyword" in tool_call_text.lower():
        keyword = ""
        keyword_match = re.search(r"'keyword':\s*'([^']*)'", tool_call_text)
        if keyword_match:
            keyword = keyword_match.group(1)
        result = {
            'name': 'search_endpoints_by_keyword',
            'args': {'keyword': keyword},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "ingest_endpoints_to_rag" in tool_call_text.lower():
        result = {
            'name': 'ingest_endpoints_to_rag',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "rag_search_endpoints" in tool_call_text.lower():
        query = ""
        top_k = 5
        query_match = re.search(r"'query':\s*'([^']*)'", tool_call_text)
        if query_match:
            query = query_match.group(1)
        top_k_match = re.search(r"'top_k':\s*(\d+)", tool_call_text)
        if top_k_match:
            top_k = int(top_k_match.group(1))
        result = {
            'name': 'rag_search_endpoints',
            'args': {'query': query, 'top_k': top_k},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "load_and_ingest_collection" in tool_call_text.lower():
        file_path = ""
        path_match = re.search(r"'file_path':\s*'([^']*)'", tool_call_text)
        if path_match:
            file_path = path_match.group(1)
        else:
            path_match = re.search(r"file_path.*?['\"]([^'\"]+)['\"]", tool_call_text)
            if path_match:
                file_path = path_match.group(1)
        result = {
            'name': 'load_and_ingest_collection',
            'args': {'file_path': file_path},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "summarize_collection" in tool_call_text.lower():
        result = {
            'name': 'summarize_collection',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "get_endpoint_details" in tool_call_text.lower():
        endpoint = ""
        endpoint_match = re.search(r"'endpoint_name':\s*'([^']*)'", tool_call_text)
        if endpoint_match:
            endpoint = endpoint_match.group(1)
        result = {
            'name': 'get_endpoint_details',
            'args': {'endpoint_name': endpoint},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "analyze_collection_methods" in tool_call_text.lower():
        result = {
            'name': 'analyze_collection_methods',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "extract_request_examples" in tool_call_text.lower():
        result = {
            'name': 'extract_request_examples',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "tavily_search" in tool_call_text.lower() or "tavily_search_results_json" in tool_call_text.lower():
        query = ""
        query_match = re.search(r"'query':\s*'([^']*)'", tool_call_text)
        if query_match:
            query = query_match.group(1)
        result = {
            'name': 'tavily_search_results_json',
            'args': {'query': query},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    elif "clear_collection" in tool_call_text.lower():
        result = {
            'name': 'clear_collection',
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    
    # If the above direct matching fails, try more general regex patterns
    name_match = re.search(r"'name':\s*'([^']*)'", tool_call_text)
    if name_match:
        tool_name = name_match.group(1)
        # Known tools - replace "Unknown Tool" with actual names
        if "collection" in tool_name.lower():
            tool_name = "load_postman_collection"
        elif "endpoint" in tool_name.lower() and "list" in tool_name.lower():
            tool_name = "list_all_endpoints" 
        elif "search" in tool_name.lower():
            tool_name = "search_endpoints_by_keyword"
        elif "tavily" in tool_name.lower():
            tool_name = "tavily_search_results_json"
        elif "summarize" in tool_name.lower():
            tool_name = "summarize_collection"
        elif "details" in tool_name.lower():
            tool_name = "get_endpoint_details"
        elif "method" in tool_name.lower():
            tool_name = "analyze_collection_methods"
        elif "example" in tool_name.lower():
            tool_name = "extract_request_examples"
        
        result = {
            'name': tool_name,
            'args': {},
            'success': True
        }
        st.session_state.last_successful_tool = result
        return result
    
    # Last resort - identify by keywords in the text
    if "endpoint" in tool_call_text.lower() and "list" in tool_call_text.lower():
        result = {'name': 'list_all_endpoints', 'args': {}, 'success': True}
        st.session_state.last_successful_tool = result
        return result
    elif "postman" in tool_call_text.lower() and "collection" in tool_call_text.lower():
        result = {'name': 'load_postman_collection', 'args': {}, 'success': True}
        st.session_state.last_successful_tool = result
        return result
    
    # Default fallback - try to use last successful tool
    print("Running default fallback, the input: ", tool_call_text)
    if 'last_successful_tool' in st.session_state:
        return st.session_state.last_successful_tool
    
    # If everything else fails, use "Response from Postman Tool" instead of generic "postman_tool"
    result = {'name': 'response_from_postman', 'args': {}, 'success': True}
    st.session_state.last_successful_tool = result
    return result

# Format tool calls in a user-friendly way
def format_tool_call(tool_call_text):
    # Parse the tool details from the tool call text
    tool_data = parse_tool_call(tool_call_text)
    
    # Map tool names to more readable versions
    tool_name_map = {
        'load_postman_collection': 'Load and Preprocess Collection',
        'list_all_endpoints': 'List Endpoints',
        'search_endpoints_by_keyword': 'Search Endpoints',
        'summarize_collection': 'Summarize Collection',
        'get_endpoint_details': 'Get Endpoint Details',
        'analyze_collection_methods': 'Analyze HTTP Methods',
        'extract_request_examples': 'Extract Request Examples',
        'ingest_endpoints_to_rag': 'Ingest to RAG',
        'rag_search_endpoints': 'RAG Semantic Search',
        'load_and_ingest_collection': 'Load & Ingest Collection',
        'tavily_search_results_json': 'Web Search',
        'tavily_search': 'Web Search',
        'postman_tool': 'Postman Tool',
        'response_from_postman': 'Response',
        'clear_collection': 'Clear Collection',
        'ask_software_engineer': 'Software Engineer',
        'ask_collection_analyst': 'Data Analyst'
    }
    
    # Get user-friendly name or use the original
    display_name = tool_name_map.get(tool_data['name'], tool_data['name'])
    
    # Format arguments in a user-friendly way
    formatted_args = ""
    for key, value in tool_data['args'].items():
        if key == 'file_path' and isinstance(value, str) and value:
            # Extract just the filename from the path for cleaner display
            filename = os.path.basename(value)
            formatted_args += f"<div><span class='tool-param'>File:</span> <span class='tool-value'>{filename}</span></div>"
        elif key == 'endpoint_name' and isinstance(value, str) and value:
            formatted_args += f"<div><span class='tool-param'>Endpoint:</span> <span class='tool-value'>{value}</span></div>"
        elif key == 'keyword' and isinstance(value, str) and value:
            formatted_args += f"<div><span class='tool-param'>Search term:</span> <span class='tool-value'>{value}</span></div>"
        elif key == 'query' and isinstance(value, str) and value:
            formatted_args += f"<div><span class='tool-param'>Query:</span> <span class='tool-value'>{value}</span></div>"
        elif key == 'top_k' and isinstance(value, int) and value:
            formatted_args += f"<div><span class='tool-param'>Results limit:</span> <span class='tool-value'>{value}</span></div>"
        elif key != 'error' and value:  # Don't display error messages or empty values
            # Default parameter display
            formatted_args += f"<div><span class='tool-param'>{key}:</span> <span class='tool-value'>{str(value)}</span></div>"
    
    # If no formatted args were created, different message based on tool
    if not formatted_args:
        if tool_data['name'] == 'list_all_endpoints':
            formatted_args = "<div><i>Retrieving all endpoints...</i></div>"
        else:
            formatted_args = ""  # Empty string instead of "No parameters needed"
    
    # Check if it's an ask tool - if so, change display format
    if tool_data['name'].startswith('ask'):
        # For 'ask' tools, show as "Talking to Agent" with a robot icon
        agent_name = display_name
        # Only do the generic replacement if we don't have a specific mapping
        if tool_data['name'] not in tool_name_map:
            agent_name = tool_data['name'].replace('ask_', '').replace('_', ' ').title()
        
        return f"""
        <div class="tool-container">
            <div class="tool-header" style="background-color: rgba(79, 148, 239, 0.15); border-bottom: 1px solid rgba(79, 148, 239, 0.25);">
                <span class="tool-icon">🤖</span>
                <span class="tool-name" style="color: var(--primary);">Talking to {agent_name}</span>
            </div>
            <div class="tool-content">
                {formatted_args}
            </div>
        </div>
        """
    else:
        # Regular tool display
        return f"""
        <div class="tool-container">
            <div class="tool-header">
                <span class="tool-icon">🔧</span>
                <span class="tool-name">{display_name}</span>
            </div>
            <div class="tool-content">
                {formatted_args}
            </div>
        </div>
        """

# Format successful responses
def format_success_message(response_text):
    """Format success responses and ensure no HTML is displayed."""
    # First, remove all HTML tags completely
    clean_text = re.sub(r'<[^>]+>', '', response_text)
    clean_text = re.sub(r'</?\w+>', '', clean_text)  # Catch any remaining tags
    
    # Remove common artifacts
    clean_text = clean_text.replace('</div>', '')
    clean_text = clean_text.replace('<div>', '')
    clean_text = clean_text.replace('<span>', '')
    clean_text = clean_text.replace('</span>', '')
    
   
    clean_text = re.sub(r' {2,}', ' ', clean_text)

    clean_text = clean_text.strip()
    
    # If the response is a success message
    if "✅" in clean_text or "success" in clean_text.lower() or "loaded" in clean_text.lower():
        return f"""
        <div class="success-container">
            <span class="success-icon"></span>
            {clean_text.replace("✅", "").strip()}
        </div>
        """
    # If it's a regular response
    else:
        return f"""
        <div class="response-container">
            <div class="response-header">
                <span class="response-icon">🧠</span>
                <span>Response</span>
            </div>
            <div class="response-content">
                {clean_text.replace("🧠 Response:", "").strip()}
            </div>
        </div>
        """

# Format endpoint lists
def format_endpoint_list(response_text):
    """Format endpoint lists and ensure no HTML is displayed."""
    # First, remove all HTML tags completely
    clean_text = re.sub(r'<[^>]+>', '', response_text)
    clean_text = re.sub(r'</?\w+>', '', clean_text)  # Catch any remaining tags
    
    # Remove common artifacts
    clean_text = clean_text.replace('</div>', '')
    clean_text = clean_text.replace('<div>', '')
    clean_text = clean_text.replace('<span>', '')
    clean_text = clean_text.replace('</span>', '')
    
    # Normalize whitespace and split into lines
    lines = [line.strip() for line in clean_text.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    if len(lines) >= 1:
        header = lines[0].replace("🧠 Response:", "").strip()
        endpoints = lines[1:] if len(lines) > 1 else []
        
        formatted_content = f"<div style='margin-bottom: 0.8rem;'>{header}</div>"
        
        if endpoints:  # Only add container if there are endpoints
            formatted_content += "<div style='max-height: 400px; overflow-y: auto;'>"
            
            for endpoint in endpoints:
                if endpoint.strip():  # Only process non-empty lines
                    formatted_content += f"<div class='list-item'>{endpoint}</div>"
            
            formatted_content += "</div>"
        else:
            formatted_content += "<div><i>No endpoints found</i></div>"
        
        return f"""
        <div class="response-container">
            <div class="response-header">
                <span class="response-icon">🧠</span>
                <span>Endpoint List</span>
            </div>
            <div class="response-content">
                {formatted_content}
            </div>
        </div>
        """
    else:
        return format_success_message(response_text)

# Function to check and create data directory if it doesn't exist
def ensure_data_directory_exists():
    # First, get the project root directory (the parent of frontend)
    current_dir = Path(os.path.abspath(__file__)).parent
    
    # Try to find the backend/data directory
    project_root = current_dir.parent  # This should be the project root
    backend_data_dir = project_root / "backend" / "data"
    
    try:
        # Create the directory if it doesn't exist
        if not backend_data_dir.exists():
            backend_data_dir.mkdir(parents=True, exist_ok=True)
            st.sidebar.success(f"Created data directory at: {backend_data_dir}")
        
        if backend_data_dir.exists() and backend_data_dir.is_dir():
            return backend_data_dir
    except Exception as e:
        st.sidebar.warning(f"Could not access {backend_data_dir}: {str(e)}")
    
    # If that fails, try from current working directory
    try:
        cwd_backend_data = Path(os.getcwd()) / "backend" / "data"
        if not cwd_backend_data.exists():
            cwd_backend_data.mkdir(parents=True, exist_ok=True)
            st.sidebar.success(f"Created data directory at: {cwd_backend_data}")
        
        if cwd_backend_data.exists() and cwd_backend_data.is_dir():
            return cwd_backend_data
    except Exception as e:
        st.sidebar.warning(f"Could not access {cwd_backend_data}: {str(e)}")
    
    # Last resort - create a local data directory in frontend folder
    try:
        local_data_dir = current_dir / "data"
        local_data_dir.mkdir(exist_ok=True)
        st.sidebar.warning(f"Using frontend/data directory as fallback: {local_data_dir}")
        return local_data_dir
    except Exception as e:
        st.sidebar.error(f"Failed to create any data directory: {str(e)}")
        st.sidebar.error("Upload functionality will not work properly.")
        return current_dir  # Return current directory as last resort

# Ensure data directory exists
data_dir = ensure_data_directory_exists()

# Sidebar for configuration and information
with st.sidebar:
    st.markdown("""
        <div class="sidebar-title">Assistant Panel</div>
        <hr class="custom-divider">
    """, unsafe_allow_html=True)
    st.markdown("<h2 class='section-header' style='margin-top: 0;'>Collection Hub</h2>", unsafe_allow_html=True)
    
    # Display the data directory info message here instead
    st.info(f"Please place the collection json file in the backend/data/collections folder")
    
    # List all JSON files in backend/data/collections
    collections_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/data/collections')))
    if collections_dir.exists() and collections_dir.is_dir():
        collection_files = [f.name for f in collections_dir.glob("*.json")]
    else:
        collection_files = []
    
    with st.container():
        selected_collection = st.selectbox(
            '',  # Remove the label
            collection_files,
            key="collection_select"
        )
        if selected_collection:
            load_cmd = f"Load the Postman collection from backend/data/collections/{selected_collection}"
            st.button(
                f"Load {selected_collection}",
                key="load_selected_collection",
                on_click=lambda: st.session_state.update({"query_input": load_cmd}),
                help="Load the selected Postman collection."
            )
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    
    # Example Queries section
    st.markdown("<h2 class='section-header' style='margin-top: 0;'>Example Queries</h2>", unsafe_allow_html=True)
    example_queries = [
        "List all endpoints in the collection",
        "Search for endpoints with the name 'generate'",
        "Show me endpoints related to inserting data into the database.",
        "Summarize this Collection",
        "What is the best tutorial for learning api so far?"
    ]
    for i, query in enumerate(example_queries):
        st.button(
            query, 
            key=f"example_query_{i}", 
            on_click=lambda q=query: st.session_state.update({"query_input": q}),
            use_container_width=True
        )
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    # Chat Controls section
    st.markdown("<h2 class='section-header'>Chat Controls</h2>", unsafe_allow_html=True)
    st.button(
        "Clear Conversation History", 
        key="clear_history", 
        on_click=lambda: st.session_state.update({"query_input": "cls"}),
        use_container_width=True
    )
    st.button(
        "Clear Collection",
        key="clear_collection_btn",
        on_click=lambda: st.session_state.update({"query_input": "Clear the loaded Postman collection from memory"}),
        use_container_width=True
    )

# Initialize session state for messages and query input
if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_input" not in st.session_state:
    st.session_state.query_input = ""

# Helper function to clear conversation history in UI
def clear_conversation_history():
    # First fully clear the messages
    st.session_state.messages = []
    
    # Call the backend endpoint to reset memory there as well
    reset_message = "Conversation history has been reset"
    try:
        response = requests.post(backend_url, json={"user_input": "cls"}, stream=True)
        for chunk in response.iter_lines():
            if chunk:
                decoded = chunk.decode("utf-8")
                if "Conversation history has been reset" in decoded:
                    # Found reset confirmation
                    reset_message = decoded
                    break
    except Exception as e:
        reset_message = "Conversation history has been reset (Note: Backend reset failed)"
        print(f"Error resetting backend memory: {str(e)}")
    
    # Add the reset notification
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"{reset_message}\n"
    })
    
    # Use rerun to completely refresh the UI (updated method)
    st.rerun()
    return True

# Main content area - simplified styling - REMOVING THE CHAT HEADER
# st.markdown("<h3 class='section-header'>💬 Chat with the Agent</h3>", unsafe_allow_html=True)
# st.markdown("Ask questions about Postman Collections or use the agent to analyze API endpoints.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Process the assistant's response
            content = message["content"]
            
            # Remove "No parameters needed" text from the content
            content = content.replace("No parameters needed", "")
            
            # Filter out system messages
            content = re.sub(r"🔄\s+Starting process.*?\n", "", content)
            content = re.sub(r"📋\s+Processing with.*?\n", "", content)
            
            # Remove sections that look like raw JSON or tool call data
            clean_content = []
            lines = content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip lines that contain raw JSON data or HTML tags
                if ((line.startswith("[{") or line.startswith("{") or line.startswith("}'")) and 
                    ("'name'" in line or '"name"' in line or "'function'" in line or '"function"' in line) and 
                    ("'args'" in line or '"args"' in line or "'arguments'" in line or '"arguments"' in line) and
                    not line.startswith("🔧 Tool Call:")):
                    i += 1
                    continue
                
                # Process tool calls
                if line.startswith("🔧 Tool Call:"):
                    tool_call_text = line[12:].strip()
                    # Try to gather additional lines if the tool call spans multiple lines
                    j = i + 1
                    while j < len(lines) and not (lines[j].startswith("🔧 Tool Call:") or lines[j].startswith("🧠 Response:")):
                        if lines[j].strip():
                            tool_call_text += " " + lines[j].strip()
                        j += 1
                    i = j - 1  # Skip the lines we've just processed
                    
                    # Handle JSON format tool calls specially
                    try:
                        if (tool_call_text.strip().startswith("{") and "function" in tool_call_text):
                            # Try to parse the {"function":"name", "arguments":{...}} format
                            json_data = json.loads(tool_call_text)
                            if "function" in json_data and "arguments" in json_data:
                                tool_name = json_data["function"]
                                args = json_data["arguments"]
                                tool_info = {"name": tool_name, "args": args, "success": True}
                                st.session_state.last_successful_tool = tool_info
                            else:
                                tool_info = parse_tool_call(tool_call_text)
                        elif (tool_call_text.strip().startswith("[") and "name" in tool_call_text):
                            # Try to parse the [{"name":"name", "args":{...}}] format
                            json_data = json.loads(tool_call_text)
                            if isinstance(json_data, list) and len(json_data) > 0:
                                first_item = json_data[0]
                                if "name" in first_item and "args" in first_item:
                                    tool_name = first_item["name"]
                                    args = first_item["args"]
                                    tool_info = {"name": tool_name, "args": args, "success": True}
                                    st.session_state.last_successful_tool = tool_info
                                else:
                                    tool_info = parse_tool_call(tool_call_text)
                            else:
                                tool_info = parse_tool_call(tool_call_text)
                        else:
                            # Use existing method
                            tool_info = parse_tool_call(tool_call_text)
                    except Exception as e:
                        tool_info = parse_tool_call(tool_call_text)
                    
                    tool_name_map = {
                        'load_postman_collection': 'Load and Preprocess Collection',
                        'list_all_endpoints': 'List Endpoints',
                        'search_endpoints_by_keyword': 'Search Endpoints',
                        'summarize_collection': 'Summarize Collection',
                        'get_endpoint_details': 'Get Endpoint Details',
                        'analyze_collection_methods': 'Analyze HTTP Methods',
                        'extract_request_examples': 'Extract Request Examples',
                        'ingest_endpoints_to_rag': 'Ingest to RAG',
                        'rag_search_endpoints': 'RAG Semantic Search',
                        'load_and_ingest_collection': 'Load & Ingest Collection',
                        'tavily_search_results_json': 'Web Search',
                        'tavily_search': 'Web Search',
                        'postman_tool': 'Postman Tool',
                        'response_from_postman': 'Response',
                        'clear_collection': 'Clear Collection',
                        'ask_software_engineer': 'Software Engineer',
                        'ask_collection_analyst': 'Data Analyst'
                    }
                    display_name = tool_name_map.get(tool_info['name'], tool_info['name'])
                    
                    # For Streamlit rendering, convert to markdown instead of HTML
                    # Check if it's an ask tool - if so, change display format
                    if tool_info['name'].startswith('ask'):
                        # For 'ask' tools, format as "Talking to Agent" with robot icon
                        agent_name = display_name
                        # Only do the generic replacement if we don't have a specific mapping
                        if tool_info['name'] not in tool_name_map:
                            agent_name = tool_info['name'].replace('ask_', '').replace('_', ' ').title()
                        
                        formatted_tool_call = f"#### 🤖 Talking to {agent_name}\n\n"
                    else:
                        # Regular tool display
                        formatted_tool_call = f"#### 🔧 Using: {display_name}\n\n"
                    
                    # Add arguments if any
                    if tool_info['args']:
                        for key, value in tool_info['args'].items():
                            if value:  # Only show non-empty arguments
                                if key == 'file_path':
                                    filename = os.path.basename(value)
                                    formatted_tool_call += f"**File:** {filename}\n\n"
                                elif key == 'endpoint_name':
                                    formatted_tool_call += f"**Endpoint:** {value}\n\n"
                                elif key == 'keyword':
                                    formatted_tool_call += f"**Search term:** {value}\n\n"
                                elif key == 'query':
                                    formatted_tool_call += f"**Query:** {value}\n\n"
                                elif key == 'top_k' and isinstance(value, int) and value:
                                    formatted_tool_call += f"**Results limit:** {value}\n\n"
                                else:
                                    formatted_tool_call += f"**{key}:** {value}\n\n"
                    else:
                        if tool_info['name'] == 'list_all_endpoints':
                            formatted_tool_call += "*Retrieving all endpoints...*\n\n"
                    
                    clean_content.append(formatted_tool_call)
                    
                # Process responses
                elif line.startswith("🧠 Response:"):
                    # Extract actual text response by removing HTML tags
                    raw_text = line[12:].strip()  # Remove "🧠 Response:" prefix
                    
                    # Continue collecting response text from following lines
                    j = i + 1
                    while j < len(lines) and not (lines[j].startswith("🔧 Tool Call:") or lines[j].startswith("🧠 Response:")):
                        if lines[j].strip():
                            raw_text += "\n" + lines[j]  # 保留原始縮排，不使用 strip()
                        j += 1
                    
                    # Clean out any HTML tags completely and convert to markdown
                    clean_text = re.sub(r'<[^>]*>', '', raw_text)
                    clean_text = clean_text.replace('</div>', '')
                    clean_text = clean_text.replace('<div>', '')
                    clean_text = clean_text.replace('</span>', '')
                    clean_text = clean_text.replace('<span>', '')
                    
                    # Format based on content
                    if "endpoints in the collection" in clean_text.lower() or "endpoint list" in clean_text.lower():
                        clean_content.append(f"#### Endpoint List\n\n{clean_text}")
                    elif "success" in clean_text.lower() or "loaded" in clean_text.lower():
                        clean_content.append(f"{clean_text}")
                    # Check for RAG search results
                    elif 'last_successful_tool' in st.session_state and st.session_state.last_successful_tool.get('name') == 'rag_search_endpoints':
                        clean_content.append(f"#### RAG Search Results\n\n{clean_text}")
                    else:
                        clean_content.append(f"#### Response\n\n{clean_text}")
                    
                    i = j - 1  # Skip processed lines
                # Process regular text
                else:
                    # Skip empty lines and HTML tags
                    if line and not line.startswith("__END__") and not (line.strip().startswith("<div") or line.strip().startswith("</div")):
                        # Clean any HTML tags
                        clean_line = re.sub(r'<[^>]+>', '', line)
                        if clean_line.strip():
                            clean_content.append(f"{clean_line}")
                
                i += 1
            
            # Join all the content with double line breaks for better readability
            if clean_content:
                clean_text = "\n\n".join(clean_content)
                st.markdown(clean_text)
            else:
                # Fallback if no clean content was generated
                # Remove all HTML tags and display as plain text
                clean_text = re.sub(r'<[^>]+>', '', content)
                clean_text = re.sub(r'</?\w+>', '', clean_text)
                st.text(clean_text)
        else:
            st.markdown(message["content"])

# Chat input area with improved placeholder
query_placeholder = "Ask about Postman Collections or how to use the agent..."
prompt = st.chat_input(query_placeholder, key="chat_input")

# Handle example query from sidebar
if st.session_state.query_input:
    prompt = st.session_state.query_input
    st.session_state.query_input = ""  # Reset after use

if prompt:
    # Normalize file paths in the prompt
    if "load_postman_collection" in prompt.lower() and prompt.startswith("Load"):
        # Fix leading slashes in file paths
        prompt = prompt.replace("/backend/data/", "backend/data/")
    
    # Check if this is a reset request
    if prompt.strip().lower() == "cls":
        # Show a processing indicator
        with st.spinner("Clearing conversation history..."):
            # First clear the front-end conversation history
            clear_conversation_history()
    else:
        # For normal messages, add to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

    # Prepare response container
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Initialize the streaming response
        collected_output = ""
        
        with st.spinner("Processing your request..."):
            try:
                response = requests.post(backend_url, json={"user_input": prompt}, stream=True)
                
                # For restart commands, check for the reset message
                is_reset_command = False
                
                for chunk in response.iter_lines():
                    if chunk:
                        decoded = chunk.decode("utf-8")
                        if decoded == "__END__":
                            break
                        elif "Conversation history has been reset" in decoded:
                            is_reset_command = True
                            # Display the reset confirmation 
                            response_placeholder.markdown(f"#### 🔄 Reset Complete\n\n{decoded}")
                            break
                        else:
                            # Skip system messages
                            if decoded.strip().startswith("🔄 Starting process") or decoded.strip().startswith("📋 Processing with"):
                                continue
                                
                            collected_output += decoded + "\n"
                            
                            # Remove any "No parameters needed" text from the output
                            collected_output = collected_output.replace("No parameters needed", "")
                            
                            # Process the streaming output
                            clean_content = []
                            lines = collected_output.split("\n")
                            i = 0
                            while i < len(lines):
                                line = lines[i].strip()
                                
                                # Skip lines that contain raw JSON data or HTML tags that aren't associated with a tool call
                                if ((line.startswith("[{") or line.startswith("{") or line.startswith("}'")) and 
                                    ("'name'" in line or '"name"' in line or "'function'" in line or '"function"' in line) and 
                                    ("'args'" in line or '"args"' in line or "'arguments'" in line or '"arguments"' in line) and
                                    not line.startswith("🔧 Tool Call:")):
                                    i += 1
                                    continue
                                
                                # Process tool calls
                                if line.startswith("🔧 Tool Call:"):
                                    # Collect the tool call information which might span multiple lines
                                    tool_call_text = line[12:].strip()
                                    j = i + 1
                                    while j < len(lines) and not (lines[j].startswith("🔧 Tool Call:") or lines[j].startswith("🧠 Response:")):
                                        if lines[j].strip():
                                            tool_call_text += " " + lines[j].strip()
                                        j += 1
                                    
                                    # Handle JSON format tool calls specially
                                    try:
                                        if (tool_call_text.strip().startswith("{") and "function" in tool_call_text):
                                            # Try to parse the {"function":"name", "arguments":{...}} format
                                            json_data = json.loads(tool_call_text)
                                            if "function" in json_data and "arguments" in json_data:
                                                tool_name = json_data["function"]
                                                args = json_data["arguments"]
                                                tool_info = {"name": tool_name, "args": args, "success": True}
                                                st.session_state.last_successful_tool = tool_info
                                            else:
                                                tool_info = parse_tool_call(tool_call_text)
                                        elif (tool_call_text.strip().startswith("[") and "name" in tool_call_text):
                                            # Try to parse the [{"name":"name", "args":{...}}] format
                                            json_data = json.loads(tool_call_text)
                                            if isinstance(json_data, list) and len(json_data) > 0:
                                                first_item = json_data[0]
                                                if "name" in first_item and "args" in first_item:
                                                    tool_name = first_item["name"]
                                                    args = first_item["args"]
                                                    tool_info = {"name": tool_name, "args": args, "success": True}
                                                    st.session_state.last_successful_tool = tool_info
                                                else:
                                                    tool_info = parse_tool_call(tool_call_text)
                                            else:
                                                tool_info = parse_tool_call(tool_call_text)
                                        else:
                                            # Use existing method
                                            tool_info = parse_tool_call(tool_call_text)
                                    except Exception as e:
                                        tool_info = parse_tool_call(tool_call_text)
                                    
                                    tool_name_map = {
                                        'load_postman_collection': 'Load and Preprocess Collection',
                                        'list_all_endpoints': 'List Endpoints',
                                        'search_endpoints_by_keyword': 'Search Endpoints',
                                        'summarize_collection': 'Summarize Collection',
                                        'get_endpoint_details': 'Get Endpoint Details',
                                        'analyze_collection_methods': 'Analyze HTTP Methods',
                                        'extract_request_examples': 'Extract Request Examples',
                                        'ingest_endpoints_to_rag': 'Ingest to RAG',
                                        'rag_search_endpoints': 'RAG Semantic Search',
                                        'load_and_ingest_collection': 'Load & Ingest Collection',
                                        'tavily_search_results_json': 'Web Search',
                                        'tavily_search': 'Web Search',
                                        'postman_tool': 'Postman Tool',
                                        'response_from_postman': 'Response',
                                        'clear_collection': 'Clear Collection',
                                        'ask_software_engineer': 'Software Engineer',
                                        'ask_collection_analyst': 'Data Analyst'
                                    }
                                    display_name = tool_name_map.get(tool_info['name'], tool_info['name'])
                                    
                                    # For Streamlit rendering, convert to markdown instead of HTML
                                    # Check if it's an ask tool - if so, change display format
                                    if tool_info['name'].startswith('ask'):
                                        # For 'ask' tools, format as "Talking to Agent" with robot icon
                                        agent_name = display_name
                                        # Only do the generic replacement if we don't have a specific mapping
                                        if tool_info['name'] not in tool_name_map:
                                            agent_name = tool_info['name'].replace('ask_', '').replace('_', ' ').title()
                                        
                                        formatted_tool_call = f"#### 🤖 Talking to {agent_name}\n\n"
                                    else:
                                        # Regular tool display
                                        formatted_tool_call = f"#### 🔧 Using: {display_name}\n\n"
                                    
                                    # Add arguments if any
                                    if tool_info['args']:
                                        for key, value in tool_info['args'].items():
                                            if value:  # Only show non-empty arguments
                                                if key == 'file_path':
                                                    filename = os.path.basename(value)
                                                    formatted_tool_call += f"**File:** {filename}\n\n"
                                                elif key == 'endpoint_name':
                                                    formatted_tool_call += f"**Endpoint:** {value}\n\n"
                                                elif key == 'keyword':
                                                    formatted_tool_call += f"**Search term:** {value}\n\n"
                                                elif key == 'query':
                                                    formatted_tool_call += f"**Query:** {value}\n\n"
                                                elif key == 'top_k' and isinstance(value, int) and value:
                                                    formatted_tool_call += f"**Results limit:** {value}\n\n"
                                                else:
                                                    formatted_tool_call += f"**{key}:** {value}\n\n"
                                    else:
                                        if tool_info['name'] == 'list_all_endpoints':
                                            formatted_tool_call += "*Retrieving all endpoints...*\n\n"
                                    
                                    clean_content.append(formatted_tool_call)
                                    i = j - 1  # Skip processed lines
                                    
                                # Process responses
                                elif line.startswith("🧠 Response:"):
                                    # Extract actual text response by removing HTML tags
                                    raw_text = line[12:].strip()  # Remove "🧠 Response:" prefix
                                    
                                    # Continue collecting response text from following lines
                                    j = i + 1
                                    while j < len(lines) and not (lines[j].startswith("🔧 Tool Call:") or lines[j].startswith("🧠 Response:")):
                                        if lines[j].strip():
                                            raw_text += "\n" + lines[j]  # 保留原始縮排，不使用 strip()
                                        j += 1
                                    
                                    # Clean out any HTML tags completely and convert to markdown
                                    clean_text = re.sub(r'<[^>]*>', '', raw_text)
                                    clean_text = clean_text.replace('</div>', '')
                                    clean_text = clean_text.replace('<div>', '')
                                    clean_text = clean_text.replace('</span>', '')
                                    clean_text = clean_text.replace('<span>', '')
                                    
                                    # Format based on content
                                    if "endpoints in the collection" in clean_text.lower() or "endpoint list" in clean_text.lower():
                                        clean_content.append(f"#### Endpoint List\n\n{clean_text}")
                                    elif "success" in clean_text.lower() or "loaded" in clean_text.lower():
                                        clean_content.append(f"{clean_text}")
                                    # Check for RAG search results
                                    elif 'last_successful_tool' in st.session_state and st.session_state.last_successful_tool.get('name') == 'rag_search_endpoints':
                                        clean_content.append(f"#### RAG Search Results\n\n{clean_text}")
                                    else:
                                        clean_content.append(f"#### Response\n\n{clean_text}")
                                    
                                    i = j - 1  # Skip processed lines
                                # Process regular text
                                else:
                                    # Skip empty lines and HTML tags
                                    if line and not line.startswith("__END__") and not (line.strip().startswith("<div") or line.strip().startswith("</div")):
                                        # Clean any HTML tags
                                        clean_line = re.sub(r'<[^>]+>', '', line)
                                        if clean_line.strip():
                                            clean_content.append(f"{clean_line}")
                                
                                i += 1
                            
                            # Join all the content with double line breaks for better readability
                            if clean_content:
                                clean_text = "\n\n".join(clean_content)
                                response_placeholder.markdown(clean_text)
                            else:
                                # Fallback if no clean content was generated
                                clean_text = re.sub(r'<[^>]+>', '', collected_output)
                                response_placeholder.text(clean_text)
                            
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {str(e)}. Make sure the backend server is running at {backend_url}")
                collected_output = f"Error connecting to backend: {str(e)}. Make sure the backend server is running."

        # Save to chat history if this wasn't a reset command
        if not is_reset_command and prompt.strip().lower() != "cls":
            st.session_state.messages.append({
                "role": "assistant",
                "content": collected_output
            })

# Format RAG search results
def format_rag_search_results(response_text):
    """Format RAG search results for better display."""
    try:
        # Try to find and parse the JSON results
        results_start = response_text.find('[{')
        results_end = response_text.rfind('}]') + 2
        
        if results_start >= 0 and results_end > results_start:
            json_str = response_text[results_start:results_end]
            results = json.loads(json_str)
            
            if results and isinstance(results, list):
                formatted_content = "<div style='margin-bottom: 0.8rem;'><b>Semantic Search Results:</b></div>"
                formatted_content += "<div style='max-height: 400px; overflow-y: auto;'>"
                
                for i, result in enumerate(results):
                    rank = result.get('rank', i+1)
                    name = result.get('name', 'Unknown Endpoint')
                    method = result.get('method', '')
                    url = result.get('url', '')
                    
                    formatted_content += f"""
                    <div style='background-color: rgba(30, 136, 229, 0.1); padding: 0.8rem; border-radius: 8px; 
                                margin-bottom: 0.8rem; border: 1px solid rgba(30, 136, 229, 0.2);'>
                        <div style='font-weight: bold; margin-bottom: 0.4rem;'>#{rank} - {name}</div>
                        <div><span style='font-weight: 500; color: #E0E0E0;'>Method:</span> <span style='color: #B0B0B0;'>{method}</span></div>
                        <div><span style='font-weight: 500; color: #E0E0E0;'>URL:</span> <span style='color: #B0B0B0;'>{url}</span></div>
                    </div>
                    """
                
                formatted_content += "</div>"
                
                return f"""
                <div class="response-container">
                    <div class="response-header">
                        <span class="response-icon">🧠</span>
                        <span>RAG Search Results</span>
                    </div>
                    <div class="response-content">
                        {formatted_content}
                    </div>
                </div>
                """
        
        # If we couldn't parse JSON or no results found, return default formatting
        return format_success_message(response_text)
    except Exception as e:
        return format_success_message(response_text)
