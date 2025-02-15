from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from .models.user import User
from google.oauth2 import id_token
from google.auth.transport import requests
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        # For development/testing, return a mock user
        # In production, you should properly validate the token
        token_parts = token.split('.')
        if len(token_parts) > 0:
            return User(
                id=token_parts[0],
                email="user@example.com",
                name="Test User"
            )
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 