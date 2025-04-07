from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import logging
from .config import settings
from .database import get_user_collection
from .services.user_service import create_user_if_not_exists
from datetime import datetime

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    users_collection = Depends(get_user_collection)
) -> dict:
    try:
        token = credentials.credentials
        logger.info("=== Starting Google Auth Process ===")
        logger.info(f"Token type: {type(token)}")
        logger.info(f"Token first 10 chars: {token[:10]}...")

        # Get user info directly using the access token
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        logger.info(f"Fetching user info from: {userinfo_endpoint}")
        
        headers = {"Authorization": f"Bearer {token}"}
        logger.info(f"Request headers: {headers}")
        
        response = requests.get(
            userinfo_endpoint,
            headers=headers
        )
        
        logger.info(f"Google API Response Status: {response.status_code}")
        logger.info(f"Google API Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info"
            )

        userinfo = response.json()
        logger.info("=== Google OAuth Response ===")
        logger.info(f"Raw userinfo: {userinfo}")
        logger.info(f"Available fields: {list(userinfo.keys())}")

        # Extract user info from Google response
        user_data = {
            "id": userinfo.get('sub'),  # Google's unique identifier
            "email": userinfo.get('email'),  # Email from Google
            "name": userinfo.get('name')  # Full name from Google
        }

        logger.info("=== Extracted User Data ===")
        logger.info(f"Final user_data to be saved: {user_data}")

        if not user_data["id"] or not user_data["email"] or not user_data["name"]:
            logger.error("Missing required user info from Google response")
            logger.error(f"id present: {bool(user_data['id'])}")
            logger.error(f"email present: {bool(user_data['email'])}")
            logger.error(f"name present: {bool(user_data['name'])}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user information from Google"
            )
        
        # Create or update user in database using create_user_if_not_exists
        logger.info("Calling create_user_if_not_exists with user_data")
        user = create_user_if_not_exists(users_collection, user_data)
        
        # Convert Pydantic model to dict if necessary
        if hasattr(user, 'model_dump'):
            user = user.model_dump()
        elif hasattr(user, 'dict'):
            user = user.dict()
            
        logger.info("=== Final User Data ===")
        logger.info(f"Final user object returned: {user}")
        logger.info("=== End Google Auth Process ===")
        
        return user

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        ) 