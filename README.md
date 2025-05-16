# Local LLM Agent System - Postman Collection Analyzer

This project demonstrates the integration of a **Local LLM Agent** with **Postman Collection** data retrieval. It creates an intelligent assistant that can analyze, search, and extract information from Postman Collections while running entirely on your local machine.

## 🌟 Key Features

- **Local LLM Integration**: Uses Ollama + Mistral for local inference without relying on cloud services
- **Streaming Agent Reasoning**: See the agent's thought process in real-time with step-by-step streaming
- **Tool-equipped AI**: Agent can use specialized tools to analyze Postman Collections
- **Beautiful UI**: Modern, responsive Streamlit interface with clean visualization of agent reasoning (includes a custom logo in `frontend/img/postman.png`)
- **Robust Error Handling**: Gracefully handles errors and provides helpful feedback
- **Collection Selection**: Select your Postman Collection JSON files from a designated folder in the UI
- **Detailed Collection Analysis**: Get statistics, HTTP method analysis, endpoint details, and more
- **Semantic Search (RAG)**: Uses HuggingFace sentence-transformers and ChromaDB for fast, persistent semantic search over endpoints

## 📦 Project Structure

```
project/
├── backend/
│   ├── main.py            # FastAPI server
│   ├── agent.py           # Agent configuration, tools, streaming
│   ├── config.py          # Configuration settings
│   ├── tools/
│   │   ├── postman_tools.py      # Postman Collection Tools
│   │   └── postman_rag_tools.py  # RAG/semantic search tools
│   ├── data/
│   │   ├── collections/   # Place your Postman Collection JSON files here
│   │   └── chroma_db/     # Persistent vector DB for semantic search
├── frontend/
│   ├── app.py             # Streamlit UI frontend
│   └── img/postman.png    # Logo image for UI
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── sample_postman_collection.json # Example collection for demo/testing
```

## 🔧 Setup Instructions

### 1. Prerequisites

- Python 3.9+ installed on your system
- Git (optional, for cloning the repository)
- Sufficient disk space (~2GB) for dependencies and models

You can check your Python version with:

```bash
python --version  # or python3 --version on some systems
```

### 2. Set Up a Virtual Environment

Setting up a virtual environment is crucial for isolating project dependencies from your system Python installation. This prevents conflicts with other Python projects.

#### Detailed Steps:

1. **Install Python venv package** (if not already available):

```bash
# For Ubuntu/Debian
sudo apt-get install python3-venv

# For macOS (using Homebrew)
brew install python3
```

2. **Create a virtual environment**:

Navigate to your project directory and run:

```bash
python -m venv venv  # Create a virtual environment named 'venv'
```

3. **Activate the virtual environment**:

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows (Command Prompt)
venv\Scripts\activate

# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

4. **Verify activation**:

You should see `(venv)` at the beginning of your command prompt. You can also verify the Python path:

```bash
which python  # macOS/Linux
where python  # Windows
```

This should point to the Python interpreter in your virtual environment.

5. **Deactivation** (when you're done working on the project):

```bash
deactivate
```

#### Troubleshooting Virtual Environment Issues:

- **PowerShell Execution Policy**: If you receive an error about execution policies on Windows, try running:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Command Not Found**: If `venv` is not recognized, ensure you have the latest Python version installed.

- **Permission Denied**: On Unix-based systems, you might need to add execute permissions:
  ```bash
  chmod +x venv/bin/activate
  ```

### 3. Install Dependencies

With your virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

This will install all the necessary dependencies listed in the requirements.txt file, including Streamlit, FastAPI, LangChain, ChromaDB, and HuggingFace sentence-transformers for semantic search.

To verify installations:

```bash
pip list
```

### 4. Set Up Environment Variables

The application uses a `.env` file to manage configuration and API keys. 

> **Note:** If there is no `env.example` file, simply create a new file named `.env` in the project root and add the following variables as needed.

```
# API Keys
TAVILY_API_KEY=your_tavily_api_key_here  # Get this from tavily.com

# LLM Configuration
LLM_MODEL=mistral-nemo
LLM_TEMPERATURE=0.1
LLM_NUM_PREDICT=128000

# Tool Configuration
TAVILY_MAX_RESULTS=5

# (Optional) Langfuse for tracing/monitoring
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

The `.env` file should be kept private and never committed to version control.

#### Troubleshooting .env Issues
- If you see errors about missing API keys or configuration, double-check your `.env` file and variable names.
- The backend will not start correctly without required keys (e.g., TAVILY_API_KEY for web search).

### 5. Install and Start Ollama (Local LLM)

If you haven't installed [Ollama](https://ollama.com/):

- Install Ollama on your machine (available for macOS, Linux, and Windows)
- Start the Ollama server
- Pull the `mistral-nemo` model:

```bash
ollama pull mistral-nemo
```

⚡ **Make sure Ollama is running in the background.**

### 6. Prepare Your Postman Collections

**Place all your Postman Collection JSON files in the following folder:**

```
backend/data/collections/
```

The application will only recognize and allow you to select collections from this folder. There is no file upload feature in the UI. You must manually copy or move your files here before starting the app.

> **A sample collection is provided:**
> - `sample_postman_collection.json` (covers basic users and products endpoints for demo/testing)

### 7. Start Backend Server (FastAPI)

From the **project root** directory:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at:

```
http://localhost:8000
```

### 8. Start Frontend Server (Streamlit)

In another terminal window:

```bash
cd frontend
streamlit run app.py
```

Frontend will be available at:

```
http://localhost:8501
```

## 🚀 How to Use

1. Open the Streamlit web UI at http://localhost:8501
2. Use the sidebar to:
   - Select a Postman Collection JSON file from the dropdown (these are the files you placed in `backend/data/collections`)
   - Try example queries with one-click buttons
3. Enter your question in the chat input field, for example:
   - "Load the Postman collection from backend/data/collections/sample_postman_collection.json"
   - "List all endpoints in the collection"
   - "Search for endpoints related to 'account'"
   - "Analyze the HTTP methods used in the collection"
   - "What kind of API is this collection for?"

4. Watch the agent:
   - Think through the problem
   - Call relevant tools
   - Return structured information
   - Provide a final answer

## 🧰 Available Tools

The agent has access to these specialized tools:

1. **list_collections**: List all available Postman Collection JSON files in `backend/data/collections`
2. **load_postman_collection**: Load and parse a Postman Collection JSON file
3. **list_all_endpoints**: List all API endpoints from the loaded collection
4. **search_endpoints_by_keyword**: Search endpoints containing a specific keyword (fuzzy search)
5. **summarize_collection**: Provide a summary of the loaded collection (with LLM-powered summary)
6. **get_endpoint_details**: Get detailed information about a specific endpoint
7. **analyze_collection_methods**: Analyze HTTP methods used in the collection
8. **extract_request_examples**: Extract and analyze request examples
9. **rag_search_endpoints**: Semantic search for endpoints using RAG (retrieval-augmented generation)
10. **web_search**: Search the web for additional information (using Tavily)
11. **clear_collection**: Clear the loaded collection from memory

## 💡 Example Queries

Here are some example queries to try:

- "List all available collections"
- "Load the Postman collection from backend/data/collections/sample_postman_collection.json"
- "What is this collection about?"
- "List all the GET endpoints"
- "Find endpoints related to users"
- "What HTTP methods are used in this collection?"
- "Explain the /accounts endpoint in detail"
- "Show me some example POST requests"
- "What authentication methods are used in this API?"


## 🔍 Troubleshooting

| Problem | Solution |
|:---|:---|
| Backend not reachable | Check if Ollama is running, port 8000 is open |
| Model missing | Run `ollama pull mistral` |
| API Key error | Make sure TAVILY_API_KEY is set correctly in your .env |
| Streamlit not updating | Refresh the browser tab |
| File selection errors | Make sure your JSON files are in `backend/data/collections` |
| Slow responses | The first query might be slow as the model loads |
| Virtual environment issues | Ensure you have the correct Python version and venv package |
| Package installation errors | Try `pip install --upgrade pip` before installing requirements |
| .env/config errors | Double-check your .env file and variable names |