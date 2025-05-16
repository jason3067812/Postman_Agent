from typing import List, Dict, Optional, Any
import json
from langchain_core.tools import tool
import os
from collections import Counter
from rapidfuzz import fuzz
from backend.config import *
import pandas as pd
from backend.schemas import *
from backend.prompt import *
from backend.tools.rag_tools import ingest_endpoints_to_rag
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import backend.store as store


def normalize_path(file_path: str) -> str:
    """
    Normalize file path by handling different formats and checking for existence.
    """
    # Remove leading slash if present
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    # Try different path combinations
    paths_to_try = [
        file_path,  # Original path (with leading slash removed if present)
        os.path.join(os.getcwd(), file_path),  # Absolute path from current directory
        os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), file_path),  # Try parent directory
    ]
    
    # If path starts with 'backend/data', also try from project root
    if file_path.startswith('backend/data'):
        # Get the project root (assuming we're in backend/tools)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        paths_to_try.append(os.path.join(project_root, file_path))
    
    # Try each path
    for path in paths_to_try:
        if os.path.exists(path):
            return path
    
    # If we got here, none of the paths exist, return the original
    return file_path


@tool("load_postman_collection", args_schema=LoadPostmanCollectionInput)
def load_postman_collection(file_path: str) -> str:
    """
    Load and parse a Postman Collection JSON file from backend/data/collections only.
    """
    
    collections_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'collections')
    print(f"[load_postman_collection] collections_dir: {collections_dir}")
    target_path = os.path.join(collections_dir, os.path.basename(file_path))
    print(f"[load_postman_collection] target_path: {target_path}")
    if not os.path.exists(target_path):
        print(f"[load_postman_collection] File not found: {target_path}")
        available_files = [f for f in os.listdir(collections_dir) if f.endswith('.json')]
        file_suggestions = "\n".join([f"- {f}" for f in available_files])
        print(f"[load_postman_collection] Available files: {available_files}")
        return f"Error: File not found: {target_path}\nAvailable files in collections directory:\n{file_suggestions}"
    try:
        print(f"[load_postman_collection] Opening file: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            store.collection_data = json.load(f)
        print(f"[load_postman_collection] Loaded JSON successfully.")
        collection_name = store.collection_data.get("info", {}).get("name", "Unnamed Collection")
        print(f"[load_postman_collection] Collection name: {collection_name}")

        # Convert to DataFrame
        def flatten_postman_items(items, parent_folder=''):
            rows = []
            for item in items:
                if 'item' in item:
                    # Folder level - recurse
                    folder_name = f"{parent_folder}/{item['name']}" if parent_folder else item['name']
                    print(f"[flatten_postman_items] Entering folder: {folder_name}")
                    rows.extend(flatten_postman_items(item['item'], folder_name))
                else:
                    request = item.get('request', {})
                    url = request.get('url', {})
                    full_url = url.get('raw', '') if isinstance(url, dict) else url
                    row = {
                        'endpoint_name': item.get('name'),
                        'endpoint_description': item.get('description'),
                        'endpoint_method': request.get('method'),
                        'endpoint_url': full_url,
                        'endpoint_headers': request.get('header', []),
                        'endpoint_body': request.get('body', {}),
                        'parent_folder': parent_folder,
                    }
                    print(f"[flatten_postman_items] Adding endpoint: {row['endpoint_name']} (method: {row['endpoint_method']}, url: {row['endpoint_url']})")
                    rows.append(row)
            return rows

        flattened = flatten_postman_items(store.collection_data.get('item', []))
        print(f"[load_postman_collection] Flattened {len(flattened)} endpoints.")
        store.collection_df = pd.DataFrame(flattened)
        print(f"[load_postman_collection] DataFrame created with shape: {store.collection_df.shape}")

        # Optional: trigger ingestion process
        try:
            print(f"[load_postman_collection] Triggering ingest_endpoints_to_rag()...")
            ingest_result = ingest_endpoints_to_rag()
            print(f"[load_postman_collection] Ingest result: {ingest_result}")
        except Exception as e:
            print(f"[load_postman_collection] Error ingesting to RAG: {str(e)}")

        return f"Collection '{collection_name}' loaded, ingested to veector db, and converted to dataframe successfully and ready for analysis."

    except json.JSONDecodeError as e:
        print(f"[load_postman_collection] JSONDecodeError: {str(e)}")
        return "Error: The file does not contain valid JSON data."
    except Exception as e:
        print(f"[load_postman_collection] Exception: {str(e)}")
        return f"Failed to load collection: {str(e)}"
    
@tool("clear_collection")
def clear_collection() -> str:
    """
    Clear the currently loaded Postman Collection from memory. No input is required.
    """
    store.collection_data = None

    return "Collection has been successfully cleared from memory."

@tool("list_all_endpoints")
def list_all_endpoints() -> List[str]:
    """
    List all API endpoints from the loaded Postman Collection.
    """

    if not store.collection_data:
        return ["No collection loaded. Please load a collection first using the load_postman_collection tool."]
    
    endpoints = []
    
    def process_items(items, parent_folder=""):
        for item in items:
            name = item.get("name", "")
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            if "request" in item:
                method = item["request"]["method"]
                url = item["request"]["url"]
                path = ""
                if isinstance(url, dict):
                    host = url.get("host", [])
                    if isinstance(host, list):
                        host = ".".join(host)
                    path_array = url.get("path", [])
                    if path_array:
                        path = "/" + "/".join(path_array)
                    elif "raw" in url:
                        path = url["raw"]
                else:
                    path = str(url)
            
                endpoints.append({
                    "parent_folder": parent_folder,
                    "name": name,
                    "method": method,
                    "path": path,
                })
            
            if "item" in item:
                process_items(item["item"], full_name)
    
    process_items(store.collection_data.get("item", []))
    
    if not endpoints:
        return ["No endpoints found in the collection."]
    
    return endpoints


@tool("search_endpoints_by_keyword", args_schema=SearchEndpointsInput)
def search_endpoints_by_keyword(keyword: str, threshold: int = 60, max_results: int = 20) -> List[str]:
    """
    Search endpoints containing a specific keyword using fuzzy matching.
    Args:
        keyword: The keyword to search for
        threshold: Similarity threshold (0-100) for fuzzy matching. Default is 60.
        max_results: Maximum number of results to return. Default is 20.
    """
    if not store.collection_data:
        return ["No collection loaded. Please load a collection first using the load_postman_collection tool."]
    
    keyword = keyword.lower()
    # Store matches with their scores
    matches_with_scores = []
    
    def search_items(items, parent_folder=""):
        for item in items:
            name = item.get("name", "").lower()
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            # Search in name with fuzzy matching
            name_score = fuzz.partial_ratio(keyword, name)
            if name_score >= threshold:
                match_info = None
                if "request" in item:
                    method = item["request"]["method"]
                    match_info = f"{method} - {full_name}"
                else:
                    match_info = f"Folder: {full_name}"
                
                if match_info:
                    matches_with_scores.append((match_info, name_score))
            
            # Search in URL and headers
            if "request" in item:
                request = item["request"]
                url = request.get("url", {})
                
                # Search in URL with fuzzy matching
                if isinstance(url, dict):
                    url_raw = url.get("raw", "").lower()
                    url_score = fuzz.partial_ratio(keyword, url_raw)
                    if url_score >= threshold:
                        match_info = f"{request.get('method', 'UNKNOWN')} {url_raw} - {full_name}"
                        matches_with_scores.append((match_info, url_score))
                
                # Search in headers
                headers = request.get("header", [])
                for header in headers:
                    header_key = header.get("key", "").lower()
                    header_value = header.get("value", "").lower()
                    
                    key_score = fuzz.partial_ratio(keyword, header_key)
                    value_score = fuzz.partial_ratio(keyword, header_value)
                    
                    if max(key_score, value_score) >= threshold:
                        match_info = f"{request.get('method', 'UNKNOWN')} {full_name} - Header: {header.get('key', '')}"
                        matches_with_scores.append((match_info, max(key_score, value_score)))
                
                # Search in body
                body = request.get("body", {})
                if body and isinstance(body, dict):
                    body_mode = body.get("mode", "")
                    if body_mode == "raw":
                        body_text = body.get("raw", "").lower()
                        body_score = fuzz.partial_ratio(keyword, body_text)
                        if body_score >= threshold:
                            match_info = f"{request.get('method', 'UNKNOWN')} {full_name} - Found in request body"
                            matches_with_scores.append((match_info, body_score))
            
            # Search in response examples
            if "response" in item:
                for resp in item["response"]:
                    resp_text = json.dumps(resp).lower()
                    resp_score = fuzz.partial_ratio(keyword, resp_text)
                    if resp_score >= threshold:
                        match_info = f"{full_name} - Found in response example"
                        matches_with_scores.append((match_info, resp_score))
            
            # Recursively search in nested items
            if "item" in item:
                search_items(item["item"], full_name)
    
    search_items(store.collection_data.get("item", []))
    
    if not matches_with_scores:
        return [f"No items found containing '{keyword}' with similarity threshold of {threshold}%."]
    
    # Sort matches by score in descending order and remove duplicates
    unique_matches = {}
    for match, score in matches_with_scores:
        if match not in unique_matches or score > unique_matches[match]:
            unique_matches[match] = score
    
    # Sort by score and format results with score
    sorted_matches = sorted(
        [(match, score) for match, score in unique_matches.items()], 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Limit results and format with score percentage
    result_matches = []
    for match, score in sorted_matches[:max_results]:
        result_matches.append(f"[Match: {score}%] {match}")
    
    return result_matches

@tool("get_endpoint_details", args_schema=EndpointDetailsInput)
def get_endpoint_details(endpoint_name: str) -> str:
    """
    Get detailed information about a specific endpoint, including parameters, headers, and example responses.
    """
    if not store.collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."
    
    endpoint_name = endpoint_name.lower()
    found_endpoint = None
    
    def find_endpoint(items, parent_folder=""):
        nonlocal found_endpoint
        for item in items:
            name = item.get("name", "").lower()
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            if endpoint_name in full_name and "request" in item:
                found_endpoint = item
                return True
            
            if "item" in item:
                if find_endpoint(item["item"], full_name):
                    return True
        
        return False
    
    find_endpoint(store.collection_data.get("item", []))
    
    if not found_endpoint:
        return f"No endpoint found with name containing '{endpoint_name}'. Try using search_endpoints_by_keyword to find the correct name."
    
    # Extract endpoint details
    name = found_endpoint.get("name", "")
    request = found_endpoint.get("request", {})
    method = request.get("method", "")
    url = request.get("url", {})
    
    # Format URL
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
    
    # Get headers
    headers = request.get("header", [])
    headers_text = "\n".join([f"- {h.get('key', '')}: {h.get('value', '')}" for h in headers]) if headers else "No headers"
    
    # Get query params
    query = url.get("query", []) if isinstance(url, dict) else []
    query_text = "\n".join([f"- {q.get('key', '')}: {q.get('value', '')}" for q in query]) if query else "No query parameters"
    
    # Get body
    body = request.get("body", {})
    body_text = "No body"
    if body and isinstance(body, dict):
        mode = body.get("mode", "")
        if mode == "raw":
            body_text = body.get("raw", "")
            if len(body_text) > 500:
                body_text = body_text[:500] + "...(truncated)"
    
    # Get responses
    responses = found_endpoint.get("response", [])
    response_text = "No example responses"
    if responses:
        response_text = f"{len(responses)} example response(s) available"
        if responses:
            sample_response = responses[0]
            sample_code = sample_response.get("code", "")
            sample_body = sample_response.get("body", "")
            if sample_body and len(sample_body) > 500:
                sample_body = sample_body[:500] + "...(truncated)"
            response_text += f"\n\nSample Response (Status: {sample_code}):\n{sample_body}"
    
    # Compose detailed output
    details = f"""
# Endpoint: {name}

- **Method**: {method}
- **URL**: {formatted_url}

## Headers
{headers_text}

## Query Parameters
{query_text}

## Request Body
```
{body_text}
```

## Responses
{response_text}
    """
    
    return details.strip()

@tool("analyze_collection_methods")
def analyze_collection_methods() -> str:
    """
    Analyze the HTTP methods used in the collection and provide statistics.
    """
    if not store.collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."
    
    methods = []
    endpoints_by_method = {}
    
    def collect_methods(items, parent_folder=""):
        for item in items:
            name = item.get("name", "")
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            if "request" in item:
                method = item["request"]["method"]
                methods.append(method)
                
                if method not in endpoints_by_method:
                    endpoints_by_method[method] = []
                
                endpoints_by_method[method].append(full_name)
            
            if "item" in item:
                collect_methods(item["item"], full_name)
    
    collect_methods(store.collection_data.get("item", []))
    
    if not methods:
        return "No endpoints with HTTP methods found in the collection."
    
    method_counts = dict(Counter(methods))
    total_endpoints = len(methods)
    
    # Sort methods by frequency
    sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare analysis
    analysis = f"# HTTP Methods Analysis\n\n"
    analysis += f"Total endpoints: {total_endpoints}\n\n"
    analysis += "## Method Distribution\n\n"
    
    for method, count in sorted_methods:
        percentage = (count / total_endpoints) * 100
        analysis += f"- **{method}**: {count} endpoints ({percentage:.1f}%)\n"
    
    analysis += "\n## Sample Endpoints by Method\n"
    
    for method, endpoints in endpoints_by_method.items():
        analysis += f"\n### {method} Endpoints\n"
        # Show up to 5 examples per method
        for endpoint in endpoints[:5]:
            analysis += f"- {endpoint}\n"
        if len(endpoints) > 5:
            analysis += f"- ... and {len(endpoints) - 5} more\n"
    
    return analysis

@tool("extract_request_examples")
def extract_request_examples() -> str:
    """
    Extract and analyze request examples from the collection.
    """
    if not store.collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."
    
    examples = []
    
    def extract_examples(items, parent_folder=""):
        for item in items:
            name = item.get("name", "")
            full_name = f"{parent_folder}/{name}" if parent_folder else name
            
            if "request" in item:
                request = item["request"]
                method = request.get("method", "")
                url = request.get("url", {})
                url_str = url.get("raw", "") if isinstance(url, dict) else str(url)
                
                body = request.get("body", {})
                body_content = None
                
                if body and isinstance(body, dict):
                    mode = body.get("mode", "")
                    if mode == "raw":
                        body_content = body.get("raw", "")
                
                example = {
                    "name": full_name,
                    "method": method,
                    "url": url_str,
                    "body": body_content
                }
                
                examples.append(example)
            
            if "item" in item:
                extract_examples(item["item"], full_name)
    
    extract_examples(store.collection_data.get("item", []))
    
    if not examples:
        return "No request examples found in the collection."
    
    # Analyze the examples
    analysis = "# Request Examples\n\n"
    
    # Group by HTTP method
    methods = {}
    for example in examples:
        method = example["method"]
        if method not in methods:
            methods[method] = []
        methods[method].append(example)
    
    for method, method_examples in methods.items():
        analysis += f"## {method} Requests\n\n"
        
        # Select up to 3 examples per method
        for i, example in enumerate(method_examples[:3]):
            analysis += f"### Example {i+1}: {example['name']}\n"
            analysis += f"- URL: {example['url']}\n"
            
            if example['body']:
                body_preview = example['body']
                if len(body_preview) > 200:
                    body_preview = body_preview[:200] + "...(truncated)"
                analysis += "- Body:\n```\n" + body_preview + "\n```\n\n"
            else:
                analysis += "- No body content\n\n"
    
    return analysis


@tool("count_endpoints")
def count_endpoints() -> str:
    """
    Count the total number of endpoints in the loaded Postman Collection and provide statistics.
    No input parameters are required for this tool.
    """
    if not store.collection_data:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."
    
    total_endpoints = 0
    folders = {}
    methods = {}
    
    def count_items(items, parent_folder=""):
        nonlocal total_endpoints
        
        for item in items:
            name = item.get("name", "")
            current_folder = f"{parent_folder}/{name}" if parent_folder else name
            
            if "request" in item:
                total_endpoints += 1
                
                # Count by folder
                folder_name = parent_folder if parent_folder else "Root"
                folders[folder_name] = folders.get(folder_name, 0) + 1
                
                # Count by HTTP method
                method = item["request"]["method"]
                methods[method] = methods.get(method, 0) + 1
            
            if "item" in item:
                count_items(item["item"], current_folder)
    
    count_items(store.collection_data.get("item", []))
    
    if total_endpoints == 0:
        return "No endpoints found in the collection."
    
    # Prepare statistics summary
    result = f"# Endpoint Count Statistics\n\n"
    result += f"Total endpoints in collection: **{total_endpoints}**\n\n"
    
    # HTTP Methods breakdown
    result += "## HTTP Methods\n"
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_endpoints) * 100
        result += f"- **{method}**: {count} endpoints ({percentage:.1f}%)\n"
    
    # Folder breakdown (top 5)
    result += "\n## Top Folders by Endpoint Count\n"
    top_folders = sorted(folders.items(), key=lambda x: x[1], reverse=True)[:5]
    for folder, count in top_folders:
        percentage = (count / total_endpoints) * 100
        result += f"- **{folder}**: {count} endpoints ({percentage:.1f}%)\n"
    
    if len(folders) > 5:
        result += f"- **Others**: {sum([count for _, count in sorted(folders.items(), key=lambda x: x[1], reverse=True)[5:]])} endpoints\n"
    
    return result



@tool("summarize_collection")
def summarize_collection() -> str:
    """
    Provide a summary of the loaded Postman Collection, including LLM-based summary.
    """

    print("[summarize_collection] Called summarize_collection tool.")

    if not store.collection_data:
        print("[summarize_collection] No collection loaded.")
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."

    try:
        print("[summarize_collection] Extracting collection info...")
        collection_info = store.collection_data.get("info", {})
        name = collection_info.get("name", "Unnamed Collection")
        description = collection_info.get("description", "No description available")
        description_short = description.split("\n")[0][:250] + "..."
        print(f"[summarize_collection] Collection name: {name}")
        print(f"[summarize_collection] Description (short): {description_short}")

        # Count endpoints and folders
        endpoints_count = 0
        folders_count = 0
        endpoint_names = []

        def count_items(items):
            nonlocal endpoints_count, folders_count, endpoint_names
            for item in items:
                if "request" in item:
                    endpoints_count += 1
                    endpoint_names.append(item.get("name", ""))
                if "item" in item:
                    folders_count += 1
                    count_items(item["item"])

        print("[summarize_collection] Counting endpoints and folders...")
        count_items(store.collection_data.get("item", []))
        print(f"[summarize_collection] Total endpoints: {endpoints_count}")
        print(f"[summarize_collection] Total folders: {folders_count}")

        # Count HTTP methods
        methods = []
        def collect_methods(items):
            for item in items:
                if "request" in item:
                    method = item["request"]["method"]
                    methods.append(method)
                if "item" in item:
                    collect_methods(item["item"])
        print("[summarize_collection] Collecting HTTP methods...")
        collect_methods(store.collection_data.get("item", []))
        method_counts = dict(Counter(methods))
        print(f"[summarize_collection] HTTP method counts: {method_counts}")
        methods_summary = ", ".join([f"{method}: {count}" for method, count in method_counts.items()])

        # Compose statistics
        statistics = f"""
# Collection Summary: {name}

## Overview
{description_short}

## Statistics
- Total Endpoints: {endpoints_count}
- Total Folders: {folders_count}
- HTTP Methods: {methods_summary}
"""

        # Prepare LLM input (truncate to 32000 characters for safety)
        endpoint_list = "\n".join(endpoint_names)
        llm_input = f"Collection Description:\n{description}\n\nEndpoint Names:\n{endpoint_list}"
        llm_input = llm_input[:32000]
        print(f"[summarize_collection] Prepared LLM input (length: {len(llm_input)})")

        # Call Ollama LLM for summary
        try:
            print("[summarize_collection] Importing summarizer_llm and preparing prompt...")
            from backend.agents import summarizer_llm

            prompt = SUMMERIZE_COLLECTION_PROMPT.format(description=description, endpoint_list=endpoint_list)
            print("[summarize_collection] Invoking summarizer_llm...")
            response = summarizer_llm.invoke([
                {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])

            llm_summary = response.content if hasattr(response, "content") else str(response)
            print("[summarize_collection] LLM summary received.")
        except Exception as e:
            print(f"[summarize_collection] LLM summary failed: {str(e)}")
            llm_summary = f"(⚠️ LLM summary failed: {str(e)})"

        print("[summarize_collection] Returning summary.")
        return statistics.strip() + "\n\n## LLM Summary (Purpose & Features)\n" + llm_summary.strip()

    except Exception as e:
        print(f"[summarize_collection] Error generating summary: {str(e)}")
        return f"Error generating summary: {str(e)}"


@tool("ask_collection_analyst", args_schema=DataframeAnalyzerInput)
def ask_collection_analyst(query: str) -> str:
    """
    Input a question and then the collection analyst will respond the answer based on the collection data.
    """

    if store.collection_df is None or store.collection_df.empty:
        return "No collection loaded. Please load a collection first using the load_postman_collection tool."
    else:
        print(store.collection_df.shape)

    from backend.agents import coder_llm

    collection_analyst_agent = create_pandas_dataframe_agent(
        coder_llm,
        store.collection_df,
        verbose=True,
        allow_dangerous_code=True,
        name="collection_analyst_agent",
    )

    result = collection_analyst_agent.invoke(input=query)

    print("Output result: ", result)

    return result


@tool("ask_software_engineer", args_schema=SoftwareEngineerInput)
def ask_software_engineer(query: str) -> str:
    """
    Ask the software engineer to write the code in the given programming language.
    """

    from backend.agents import coder_llm

    answer = coder_llm.invoke([
        {"role": "system", "content": SOFTWARE_ENGINEER_SYSTEM_PROMPT},
        {"role": "user", "content": query + "\n\n" + "Let's think step by step."}
    ]).content

    print("Output result: ", answer)

    return answer

    

