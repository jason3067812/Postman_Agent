from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import json
import time
from backend.config import *
from langfuse.client import Langfuse
from langfuse.callback import CallbackHandler
import re

os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_CONFIG["langfuse_public_key"]
os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_CONFIG["langfuse_secret_key"]
os.environ["LANGFUSE_HOST"] = LANGFUSE_CONFIG["langfuse_host"]
os.environ["TAVILY_API_KEY"] = TOOL_CONFIG["tavily_api_key"]

from backend.tools.postman_tools import (
    load_postman_collection,
    list_all_endpoints,
    search_endpoints_by_keyword,
    summarize_collection,
    get_endpoint_details,
    analyze_collection_methods,
    extract_request_examples,
    list_collections,
    clear_collection,
    count_endpoints,
    dataframe_analyzer,
)

from backend.tools.postman_rag_tools import (
    rag_search_endpoints,
)

from backend.prompt import MAIN_REACT_AGENT_SYSTEM_PROMPT

def remove_angle_brackets_around_url(text):
    # This matches <http://...> or <https://...> and removes the angle brackets
    return re.sub(r'<(https?://[^>]+)>', r'\1', text)

# Setup LLM
react_agent = ChatOllama(
    model=MEDIUM_MODEL,
    num_predict=OUTPUT_TOKENS,
    verbose=True,
    **BALANCED_DECODER_SETTINGS
)

# Setup Tavily tool with error handling
tavily_tool = TavilySearchResults(
    max_results=TOOL_CONFIG["tavily_max_results"],
)

# Collection of tools with better descriptions
tools = [
    tavily_tool,
    load_postman_collection,
    clear_collection,
    list_all_endpoints,
    search_endpoints_by_keyword,
    summarize_collection,
    get_endpoint_details,
    analyze_collection_methods,
    extract_request_examples,
    rag_search_endpoints,
    list_collections,
    count_endpoints,
    dataframe_analyzer,
]

# Enhanced prompt template for better agent performance
system_prompt = MAIN_REACT_AGENT_SYSTEM_PROMPT

# Setup Memory with maximum history limit
chat_history = ChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=chat_history,
    return_messages=True,
    memory_key=MEMORY_CONFIG["memory_key"],
    max_token_limit=MEMORY_CONFIG.get("max_token_limit", 4096),
)

# Create prompt with the enhanced system message
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="messages"),
])

# Build agent graph with enhanced prompt
graph = create_react_agent(react_agent, tools=tools, prompt=prompt)

def reset_memory():
    """
    Reset the chat memory by creating a new ChatMessageHistory object
    and updating the memory with it.
    """
    global chat_history, memory
    chat_history = ChatMessageHistory()
    memory = ConversationBufferMemory(
        chat_memory=chat_history,
        return_messages=True,
        memory_key=MEMORY_CONFIG["memory_key"],
    )
    return "Conversation history has been reset"

def agent_stream(user_input: str):
    """
    Stream agent reasoning steps and final response with enhanced error handling.
    """
    # Check if this is a restart command
    if user_input.strip().lower() == "cls":
        reset_message = reset_memory()
        yield f"🔄 {reset_message}\n"
        yield "__END__"
        return
        
    start_time = time.time()
    
    try:
        # Prepare input messages including memory
        inputs = {"messages": memory.chat_memory.messages + [("user", user_input)]}
        
        langfuse_handler = CallbackHandler(trace_name="/chat/")

        # Stream the agent's response
        stream = graph.stream(input=inputs, stream_mode="values", config={"callbacks": [langfuse_handler]})

        final_response = ""
        tool_calls_made = 0
        for s in stream:
            message = s["messages"][-1]
            if message.type == "ai":
                if isinstance(message, tuple):
                    log_text = f"Tuple Message: {message}"
                    print(log_text)
                    yield log_text + "\n"
                else:
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls_made += 1
                        log_text = f"🔧 Tool Call:\n{message.tool_calls}"
                        print("log_text", log_text)
                        yield log_text + "\n"
                    else:
                        final_response = message.content
                        final_response = remove_angle_brackets_around_url(final_response)

                        log_text = f"🧠 Response:\n{final_response}"
                        print("log_text", log_text)
                        yield log_text + "\n"
                        

        # Update memory after stream finished
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(final_response)
        
        # Performance metrics
        elapsed_time = time.time() - start_time
        log_text = f"⏱️ Process completed in {elapsed_time:.2f} seconds with {tool_calls_made} tool calls"
        print(log_text)

    except Exception as e:
        error_message = f"🚫 Error: {str(e)}\n\nI encountered a problem while processing your request. Please try again or rephrase your question."
        yield error_message + "\n"
        print(f"Agent error: {str(e)}")

    # Mark final output (for FE side to know it ends)
    yield "__END__"