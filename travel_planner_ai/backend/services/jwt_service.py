import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from ..config import settings

logger = logging.getLogger(__name__)

class JWTService:
    def __init__(self):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.expires_minutes = settings.jwt_expires_minutes
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create a JWT access token for the user
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            str: JWT token
        """
        try:
            # Create expiration time
            expire = datetime.utcnow() + timedelta(minutes=self.expires_minutes)
            
            # Create payload
            payload = {
                "sub": user_data.get("id") or user_data.get("_id"),  # Subject (user ID)
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "exp": expire,  # Expiration time
                "iat": datetime.utcnow(),  # Issued at
                "type": "access"
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created JWT access token for user: {user_data.get('email')}")
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    def create_refresh_token(self, user_id: str) -> str:
        """
        Create a JWT refresh token for the user
        
        Args:
            user_id: User ID
            
        Returns:
            str: JWT refresh token
        """
        try:
            # Refresh tokens have longer expiration (7 days)
            expire = datetime.utcnow() + timedelta(days=7)
            
            payload = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh"
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Created JWT refresh token for user: {user_id}")
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating JWT refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create refresh token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Dict: Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is expired
            if datetime.utcnow() > datetime.utcfromtimestamp(payload["exp"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Error verifying JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def refresh_access_token(self, refresh_token: str, users_collection) -> str:
        """
        Create a new access token using a refresh token
        
        Args:
            refresh_token: JWT refresh token
            users_collection: MongoDB users collection
            
        Returns:
            str: New JWT access token
        """
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user data from database
            user = users_collection.find_one({"_id": user_id})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Create new access token
            new_access_token = self.create_access_token(user)
            
            return new_access_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh token"
            )

# Create global instance
jwt_service = JWTService() 