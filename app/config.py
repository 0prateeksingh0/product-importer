"""
Application configuration module.
Loads environment variables and provides configuration settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/product_importer"
    
    # Redis (optional - only needed for CSV imports with Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery (optional - only needed for async CSV imports)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Application
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://localhost:3000"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    
    # Batch Processing
    BATCH_SIZE: int = 1000  # Process CSV in batches of 1000 records
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

