import logging
from typing import Optional, Tuple
from google.oauth2 import id_token
from google.auth.transport import requests
from pymongo.collection import Collection
from fastapi import HTTPException, status

from ..models.user import User
from .user_service import create_user_if_not_exists

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, users_collection: Collection, google_client_id: str):
        self.users_collection = users_collection
        self.google_client_id = google_client_id
        
    async def verify_google_token(self, token: str) -> Tuple[str, str, Optional[str]]:
        """
        Verify Google OAuth token and extract user information
        
        Args:
            token: Google ID token
            
        Returns:
            Tuple containing (google_id, email, name)
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            id_info = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Extract user info from token
            google_id = id_info["sub"]
            email = id_info["email"]
            name = id_info.get("name")  # Optional
            
            return google_id, email, name
            
        except ValueError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    async def authenticate_user(self, token: str) -> User:
        """
        Authenticate user with Google token and create/update user record
        
        Args:
            token: Google ID token
            
        Returns:
            User: Authenticated user object
        """
        # Verify token and get user info
        google_id, email, name = await self.verify_google_token(token)
        
        # Create user data dict
        user_data = {
            "id": google_id,
            "email": email,
            "name": name or "New User"  # Fallback if name not provided
        }
        
        # Create or update user
        user = await create_user_if_not_exists(self.users_collection, user_data)
        
        return user 