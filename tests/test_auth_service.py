import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from google.auth.transport import requests

from travel_planner_ai.backend.services.auth_service import AuthService
from travel_planner_ai.backend.models.user import User

@pytest.fixture
def mock_users_collection():
    return Mock()

@pytest.fixture
def auth_service(mock_users_collection):
    return AuthService(mock_users_collection, "test-client-id")

@pytest.mark.asyncio
async def test_verify_google_token_success():
    # Mock data
    token = "valid-token"
    google_id = "123"
    email = "test@example.com"
    name = "Test User"
    
    # Create mock id_token.verify_oauth2_token response
    mock_id_info = {
        "sub": google_id,
        "email": email,
        "name": name
    }
    
    with patch("google.oauth2.id_token.verify_oauth2_token", return_value=mock_id_info):
        auth_service = AuthService(Mock(), "test-client-id")
        result = await auth_service.verify_google_token(token)
        
        assert result == (google_id, email, name)

@pytest.mark.asyncio
async def test_verify_google_token_invalid():
    with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("Invalid token")):
        auth_service = AuthService(Mock(), "test-client-id")
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_google_token("invalid-token")
        
        assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_authenticate_user_new_user(auth_service, mock_users_collection):
    # Mock data
    token = "valid-token"
    google_id = "123"
    email = "test@example.com"
    name = "Test User"
    
    # Mock verify_google_token
    with patch.object(auth_service, "verify_google_token", 
                     return_value=(google_id, email, name)):
        
        # Mock user creation
        expected_user = User(
            id=google_id,
            email=email,
            name=name,
            available_credits=1
        )
        mock_users_collection.find_one.return_value = None
        mock_users_collection.insert_one.return_value = None
        
        # Test authentication
        user = await auth_service.authenticate_user(token)
        
        assert user.id == google_id
        assert user.email == email
        assert user.name == name
        assert user.available_credits == 1 