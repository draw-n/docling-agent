import os
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with validation."""
    
    # API Configuration
    api_title: str = "Docling Assistant API"
    api_version: str = "0.1.0"
    api_description: str = "Backend API for a Docling-focused agentic RAG assistant."
    
    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4"
    ollama_timeout: int = 120
    ollama_max_retries: int = 3
    ollama_retry_delay: float = 1.0
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Qdrant Configuration
    use_qdrant: bool = True
    qdrant_collection: str = "docling_docs"
    qdrant_path: str = "qdrant_data"
    
    # Request Configuration
    max_query_length: int = 1000
    request_timeout: int = 30
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Made with Bob