from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import logging
from .config import settings
from .database import get_user_collection
from .services.user_service import create_user_if_not_exists

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    users_collection = Depends(get_user_collection)
) -> dict:
    try:
        token = credentials.credentials
        logger.info("Received access token")

        # Get user info directly using the access token
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info"
            )

        userinfo = response.json()
        logger.info(f"Successfully retrieved user info for: {userinfo.get('email')}")

        # Prepare user data
        user_data = {
            "id": userinfo['sub'],
            "email": userinfo['email'],
            "name": userinfo.get('name', '')
        }
        
        # Create user if not exists (this will grant 1 free credit on first signup)
        await create_user_if_not_exists(users_collection, user_data)
        
        return user_data

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        ) 