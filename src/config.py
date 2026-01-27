"""
Configuration Management for Social Support AI Application

This module handles all configuration settings using Pydantic for validation
and environment variables for flexibility.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        ollama_base_url: Base URL for Ollama LLM server
        ollama_model: Model name to use (e.g., llama3.2, mistral)
        sqlite_db_path: Path to SQLite database file
        chroma_persist_dir: Directory for ChromaDB persistence
        langfuse_public_key: Langfuse public key for observability
        langfuse_secret_key: Langfuse secret key
        langfuse_host: Langfuse server host
        debug: Enable debug mode
        log_level: Logging level
    """
    
    def __init__(self):
        # Ollama LLM Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        # Database Configuration
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", "./data/social_support.db")
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        
        # Langfuse Observability
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Application Settings
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Paths
        self.upload_dir = os.getenv("UPLOAD_DIR", "./data/uploads")
        self.synthetic_data_dir = os.getenv("SYNTHETIC_DATA_DIR", "./data/synthetic")
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.synthetic_data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


# Eligibility Criteria Configuration
ELIGIBILITY_CRITERIA = {
    "max_income_threshold": 15000,  # Monthly income in AED
    "min_family_size_for_bonus": 3,
    "asset_liability_ratio_threshold": 0.5,
    "credit_score_minimum": 300,
    "employment_weights": {
        "employed": 0.8,
        "self_employed": 0.7,
        "unemployed": 1.0,  # Higher weight = more need
        "retired": 0.9
    }
}

# Economic Enablement Programs
ENABLEMENT_PROGRAMS = {
    "upskilling": [
        "Digital Skills Training",
        "Financial Literacy Course",
        "Vocational Training Program",
        "Language Enhancement Course"
    ],
    "job_matching": [
        "Government Job Portal Registration",
        "Private Sector Job Fair",
        "Freelance Opportunities Platform"
    ],
    "career_counseling": [
        "One-on-One Career Guidance",
        "Resume Building Workshop",
        "Interview Preparation Session"
    ]
}
