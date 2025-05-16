from typing import List, Dict, Any, Optional
import os
import json
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import chromadb
from chromadb import PersistentClient
from langchain_community.embeddings import HuggingFaceEmbeddings
import uuid
from pathlib import Path
from backend.tools.postman_tools import LoadPostmanCollectionInput

# Global variables
chroma_client = None
collection = None
collection_loaded = False

class RAGSearchEndpointsInput(BaseModel):
    query: str = Field(..., description="The search query to find relevant endpoints.")
    top_k: int = Field(5, description="Number of top results to return.")

def initialize_chroma():
    """Initialize the ChromaDB client and create a persistent directory if it doesn't exist."""
    global chroma_client
    
    # Create data directory if it doesn't exist
    persist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma_db")
    os.makedirs(persist_directory, exist_ok=True)
    
    # Initialize ChromaDB client with persistence (NEW)
    chroma_client = PersistentClient(path=persist_directory)
    
    return chroma_client

def get_embeddings_model():
    """Get the HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

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
                
                # Create a comprehensive description
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
            
            # Process nested items recursively
            if "item" in item:
                process_items(item["item"], full_name)
    
    process_items(collection_data.get("item", []))
    return endpoints_data

def ingest_endpoints_to_rag() -> str:
    """
    Ingest endpoints from the loaded Postman collection into the RAG system.
    This creates embeddings for endpoint names and descriptions and stores them in ChromaDB.
    """
    global chroma_client, collection, collection_loaded

    # Check if collection data is available from postman_tools
    from backend.tools.postman_tools import collection_data
    if not collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."

    try:
        # Initialize ChromaDB if not already done
        if chroma_client is None:
            chroma_client = initialize_chroma()

        # Create or get collection
        collection_name = collection_data.get("info", {}).get("name", "postman_collection")
        collection_name = collection_name.replace(" ", "_").lower()

        # Try to get existing collection, or create a new one
        try:
            collection = chroma_client.get_collection(name=collection_name)
            # Delete existing collection to refresh data
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        # Create a new collection
        embeddings_model = get_embeddings_model()
        collection = chroma_client.create_collection(name=collection_name)

        # Extract endpoints data
        endpoints_data = extract_endpoints_data(collection_data)

        if not endpoints_data:
            return "No endpoints found in the collection to ingest."

        # Prepare data for ingestion
        ids = []
        documents = []
        metadatas = []

        for endpoint in endpoints_data:
            ids.append(endpoint["id"])
            # The text to embed contains both name and description for better matching
            documents.append(f"{endpoint['name']}\n{endpoint['description']}")
            metadatas.append({
                "name": endpoint["name"],
                "method": endpoint["method"],
                "url": endpoint["url"]
            })

        # Add data to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        collection_loaded = True
        return f"✅ Successfully ingested {len(endpoints_data)} endpoints into RAG system."

    except Exception as e:
        return f"Error during ingestion: {str(e)}"

@tool("rag_search_endpoints", args_schema=RAGSearchEndpointsInput)
def rag_search_endpoints(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Search for relevant endpoints using RAG (Retrieval Augmented Generation).
    Returns 5 ~ 10 endpoints that are semantically similar to the query, including similarity scores.
    """
    global chroma_client, collection, collection_loaded
    
    if not collection_loaded:
        result = ingest_endpoints_to_rag()
        if "Successfully" not in result:
            return [{"error": result}]
    
    try:
        # Initialize embeddings model
        embeddings_model = get_embeddings_model()
        # Embed the query using the same model as used for indexing
        query_embedding = embeddings_model.embed_query(query)
        print(f"Query embedding: {query_embedding}")
        # ChromaDB expects a list of embeddings
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        print(f"Retrieved results: {results}")
        if not results["ids"][0]:
            return [{"message": "No relevant endpoints found."}]
        # Try to get similarity scores (ChromaDB may return 'distances' or 'scores')
        scores = results.get("distances") or results.get("scores")
        # If distances, convert to similarity (assuming cosine: similarity = 1 - distance)
        if scores is not None:
            scores = scores[0]  # First query
            similarities = [1 - d if d is not None else None for d in scores]
        else:
            similarities = [None] * len(results["ids"][0])
        # Format results with similarity score
        formatted_results = []
        for i, (doc_id, document, metadata, sim) in enumerate(zip(
            results["ids"][0], results["documents"][0], results["metadatas"][0], similarities)):
            result = {
                "rank": i + 1,
                "name": metadata["name"],
                "method": metadata["method"],
                "url": metadata["url"],
                "document": document,
                "similarity": round(sim, 4) if sim is not None else None
            }
            formatted_results.append(result)
        # Sort by similarity descending (if available)
        formatted_results.sort(key=lambda x: x["similarity"] if x["similarity"] is not None else 0, reverse=True)

        print(f"Formatted results: {formatted_results}")

        return formatted_results
    except Exception as e:
        return [{"error": f"Error during search: {str(e)}"}]
