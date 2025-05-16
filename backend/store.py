"""
Module to store shared state between different parts of the application.
"""

# Shared state variables
collection_data = None
collection_df = None 

# ChromaDB-related variables
chroma_client = None
chroma_collection = None
collection_loaded_to_rag = False


