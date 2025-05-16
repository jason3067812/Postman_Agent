from typing import List, Dict, Any, Optional
import os
import json
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import chromadb
from chromadb import PersistentClient
import uuid
from pathlib import Path
from backend.schemas import RAGSearchEndpointsInput
import backend.store as store
from chromadb.utils import embedding_functions
default_ef = embedding_functions.DefaultEmbeddingFunction()

def initialize_chroma():
    """Initialize the ChromaDB client and create a persistent directory if it doesn't exist."""

    persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_db")
    os.makedirs(persist_directory, exist_ok=True)
    store.chroma_client = PersistentClient(path=persist_directory)
    
    return store.chroma_client


def extract_endpoints_data(collection_data):
    """Extract endpoint data from Postman collection for RAG indexing."""
    endpoints_data = []
    
    def process_items(items, parent_folder=""):
        for item in items:
            name = item.get("name", "")
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            if "request" in item:
                # This is an endpoint
                request = item["request"]
                method = request.get("method", "")
                url = request.get("url", {})
                
                # Extract URL
                formatted_url = ""
                if isinstance(url, dict):
                    if "raw" in url:
                        formatted_url = url["raw"]
                    else:
                        host = url.get("host", [])
                        if isinstance(host, list):
                            host = ".".join(host)
                        path = url.get("path", [])
                        if path:
                            path = "/" + "/".join(path)
                            formatted_url = f"{host}{path}"
                else:
                    formatted_url = str(url)
                
                # Extract description from item
                description = item.get("description", "")
                
                # Extract query parameters
                query_params = []
                if isinstance(url, dict) and "query" in url:
                    for param in url["query"]:
                        param_desc = f"{param.get('key', '')}: {param.get('description', '')}"
                        query_params.append(param_desc)
                
                # Extract headers
                headers = []
                for header in request.get("header", []):
                    header_desc = f"{header.get('key', '')}: {header.get('description', '')}"
                    headers.append(header_desc)
                
                # Extract body if available
                body_text = ""
                body = request.get("body", {})
                if body and isinstance(body, dict):
                    mode = body.get("mode", "")
                    if mode == "raw":
                        body_text = body.get("raw", "")[:200]  # Truncate to avoid too much text
                
                comprehensive_description = f"Method: {method}\nURL: {formatted_url}\n"
                if description:
                    comprehensive_description += f"Description: {description}\n"
                if query_params:
                    comprehensive_description += f"Query Parameters: {', '.join(query_params)}\n"
                if headers:
                    comprehensive_description += f"Headers: {', '.join(headers)}\n"
                if body_text:
                    comprehensive_description += f"Body Preview: {body_text}\n"
                
                endpoint_data = {
                    "id": str(uuid.uuid4()),
                    "name": full_name,
                    "method": method,
                    "url": formatted_url,
                    "description": comprehensive_description
                }
                
                endpoints_data.append(endpoint_data)
            
            if "item" in item:
                process_items(item["item"], full_name)
    
    process_items(collection_data.get("item", []))
    return endpoints_data

def ingest_endpoints_to_rag() -> str:
    """
    Ingest endpoints from the loaded Postman collection into the RAG system.
    This creates embeddings for endpoint names and descriptions and stores them in ChromaDB.
    """
    if not store.collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."

    try:
        if store.chroma_client is None:
            store.chroma_client = initialize_chroma()

        collection_name = store.collection_data.get("info", {}).get("name", "postman_collection")
        collection_name = collection_name.replace(" ", "_").lower()

        try:
            store.chroma_collection = store.chroma_client.get_collection(name=collection_name)
            store.chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        store.chroma_collection = store.chroma_client.create_collection(name=collection_name, embedding_function=default_ef)

        endpoints_data = extract_endpoints_data(store.collection_data)

        if not endpoints_data:
            return "No endpoints found in the collection to ingest."

   
        ids = []
        documents = []
        metadatas = []

        for endpoint in endpoints_data:
            ids.append(endpoint["id"])
            documents.append(f"{endpoint['name']}\n{endpoint['description']}")
            metadatas.append({
                "name": endpoint["name"],
                "method": endpoint["method"],
                "url": endpoint["url"]
            })

        store.chroma_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        store.collection_loaded_to_rag = True
        return f"Successfully ingested {len(endpoints_data)} endpoints into RAG system."

    except Exception as e:
        return f"Error during ingestion: {str(e)}"

@tool("rag_search_endpoints", args_schema=RAGSearchEndpointsInput)
def rag_search_endpoints(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Search for relevant endpoints using RAG (Retrieval Augmented Generation).
    Returns 5 ~ 10 endpoints that are semantically similar to the query, including similarity scores.
    """
    if not store.collection_loaded_to_rag:
        result = ingest_endpoints_to_rag()
        if "Successfully" not in result:
            return [{"error": result}]
    
    try:
        results = store.chroma_collection.query(
            query_texts=[query],
            n_results=top_k,
            include=['documents', 'metadatas']
        )

        formatted_results = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i in range(len(documents)):
            result = {
                "document": documents[i] if i < len(documents) else None,
                "metadata": metadatas[i] if i < len(metadatas) else None,
            }
            formatted_results.append(result)

        print(f"Formatted results: {formatted_results}")

        return formatted_results
    except Exception as e:
        return [{"error": f"Error during search: {str(e)}"}]
