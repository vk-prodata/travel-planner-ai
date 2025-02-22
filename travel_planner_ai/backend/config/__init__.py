# Empty file to make the directory a Python package 

from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseModel):
    # MongoDB settings
    mongodb_uri: str = os.getenv("MONGODB_URI")
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    
    # Google Auth settings
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID")
    
    # JWT settings
    jwt_secret: str = os.getenv("JWT_SECRET", "your-super-secret-key-change-this-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24  # 24 hours

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Log loaded settings (without sensitive values)
        logger.info(f"Loaded settings: MongoDB URI: {'set' if self.mongodb_uri else 'not set'}, "
                   f"Google Client ID: {'set' if self.google_client_id else 'not set'}, "
                   f"OpenAI API Key: {'set' if self.openai_api_key else 'not set'}")
        
        # Validate required settings
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not self.google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")

# Create settings instance
settings = Settings()

# Export settings
__all__ = ['settings'] 