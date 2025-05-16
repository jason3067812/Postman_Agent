from pydantic import BaseModel, Field

class LoadPostmanCollectionInput(BaseModel):
    file_path: str = Field(..., description="Path to the Postman Collection JSON file.")

class SearchEndpointsInput(BaseModel):
    keyword: str = Field(..., description="Keyword to search within endpoints.")
    threshold: int = Field(60, description="Similarity threshold (0-100) for fuzzy matching. Default is 60.")
    max_results: int = Field(20, description="Maximum number of results to return. Default is 20.")

class EndpointDetailsInput(BaseModel):
    endpoint_name: str = Field(..., description="Name of the endpoint to get details for.")

class DataframeAnalyzerInput(BaseModel):
    query: str = Field(..., description="The user query in natural language text format.") 