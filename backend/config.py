"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# MODEL NAMES
SMALL_MODEL="phi4-mini"         # does not support tool usage, suitable for routing
MEDIUM_MODEL="mistral-nemo"     # supports tool usage
LARGE_MODEL="phi4"              # does not support tool usage, suitable for coding and other more complex tasks

# hyperparams
CONCISE_DECODER_SETTINGS = {
    "temperature": 0,
}

BALANCED_DECODER_SETTINGS = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 30
}
CREATIVE_DECODER_SETTINGS = {
    "temperature": 0.7,
    "top_p": 0.99,
    "top_k": 40
}


OUTPUT_TOKENS = 128000

# Tool Configuration
TAVILY_MAX_RESULTS=5
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY", "")

# Tool Configuration
TOOL_CONFIG = {
    "tavily_max_results": TAVILY_MAX_RESULTS,
    "tavily_api_key": TAVILY_API_KEY
}

# Langfuse Configuration
LANGFUSE_CONFIG = {
    "langfuse_public_key": os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    "langfuse_secret_key": os.getenv("LANGFUSE_SECRET_KEY", ""),
    "langfuse_host": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
}

MEMORY_CONFIG = {
    "memory_key": "messages",
    "max_token_limit": 4096,
    "k": 30
}
