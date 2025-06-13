import os
from typing import List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://eindr:password@localhost/eindr_db")
    postgres_user: str = os.getenv("POSTGRES_USER", "eindr")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_db: str = os.getenv("POSTGRES_DB", "eindr_db")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # App settings
    app_name: str = "Eindr Email Capture API"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://eindr.com",
        "https://www.eindr.com"
    ]
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Security settings
    force_https: bool = environment == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 