from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User question about Docling"
    )
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize the query."""
        # Strip whitespace
        v = v.strip()
        
        # Check for empty after stripping
        if not v:
            raise ValueError("Query cannot be empty or only whitespace")
        
        # Check length
        if len(v) > 1000:
            raise ValueError("Query exceeds maximum length of 1000 characters")
        
        return v


class Citation(BaseModel):
    title: str
    url: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool


class RefreshResponse(BaseModel):
    status: str
    documents_indexed: int
    collection_name: str
    backend: str

# Made with Bob
