import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from bson import ObjectId
from travel_planner_ai.backend.main import app
from travel_planner_ai.backend.models.user import CreditsPackage

client = TestClient(app)

# Mock user for authentication
mock_user = {
    "id": "test-user-id",
    "email": "test@example.com",
    "name": "Test User",
    "available_credits": 5,
    "total_credits_purchased": 10,
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Mock credits packages
mock_packages = [
    CreditsPackage(
        id="basic",
        name="Basic Package",
        credits=10,
        price=1.00,
        is_popular=False
    ),
    CreditsPackage(
        id="value",
        name="Value Package",
        credits=100,
        price=39.99,
        is_popular=True
    )
]

# Mock response for userinfo endpoint
mock_userinfo_response = MagicMock()
mock_userinfo_response.status_code = 200
mock_userinfo_response.json.return_value = {
    "sub": mock_user["id"],
    "email": mock_user["email"],
    "name": mock_user["name"]
}

# Mock Stripe payment intent
class MockPaymentIntent:
    def __init__(self):
        self.id = "pi_test_123456"
        self.client_secret = "test_secret"
        self.status = "succeeded"
        self.metadata = {
            "credits": "10",
            "package_id": "basic",
            "quantity": "1"
        }

# Mock Stripe API calls
@pytest.fixture(autouse=True)
def mock_stripe():
    mock_intent = MockPaymentIntent()
    with patch("stripe.PaymentIntent.create", return_value=mock_intent):
        with patch("stripe.PaymentIntent.retrieve", return_value=mock_intent):
            yield

# Mock the authentication dependency
@pytest.fixture(autouse=True)
def mock_auth():
    with patch("travel_planner_ai.backend.routers.credits.get_current_user", return_value=mock_user):
        with patch("requests.get", return_value=mock_userinfo_response):
            with patch("travel_planner_ai.backend.auth.create_user_if_not_exists", return_value=None):
                yield

# Simplified approach: patch the service functions directly
@pytest.fixture(autouse=True)
def mock_services():
    # Mock for get_user_credits
    async def mock_get_user_credits(*args, **kwargs):
        return {
            "available_credits": mock_user["available_credits"],
            "total_credits_purchased": mock_user["total_credits_purchased"]
        }
    
    # Mock for add_credits
    async def mock_add_credits(*args, **kwargs):
        return {
            "available_credits": mock_user["available_credits"] + 10,
            "total_credits_purchased": mock_user["total_credits_purchased"] + 10
        }
    
    # Mock for get_credits_packages
    async def mock_get_packages(*args, **kwargs):
        return mock_packages
    
    # Mock for create_payment_intent
    async def mock_create_intent(package_id: str, quantity: int = 1):
        package = next((p for p in mock_packages if p.id == package_id), None)
        return {
            "client_secret": "test_secret",
            "package": package.dict(),
            "quantity": quantity,
            "total_credits": package.credits * quantity,
            "total_amount": package.price * quantity
        }
    
    # Mock for verify_payment_intent
    async def mock_verify_intent(payment_intent_id: str):
        return {
            "verified": True,
            "status": "succeeded",
            "metadata": {
                "credits": "10",
                "package_id": "basic",
                "quantity": "1"
            }
        }
    
    # Patch all the service functions directly
    with patch("travel_planner_ai.backend.routers.credits.get_user_credits", new=mock_get_user_credits):
        with patch("travel_planner_ai.backend.routers.credits.add_credits", new=mock_add_credits):
            with patch("travel_planner_ai.backend.services.credits_service.get_credits_packages", new=mock_get_packages):
                with patch("travel_planner_ai.backend.services.credits_service.create_payment_intent", new=mock_create_intent):
                    with patch("travel_planner_ai.backend.services.credits_service.verify_payment_intent", new=mock_verify_intent):
                        yield

def test_get_user_credits(mock_services):
    """Test getting user credits"""
    response = client.get("/credits", headers={"Authorization": "Bearer fake-token"})
    
    assert response.status_code == 200
    data = response.json()
    assert "available_credits" in data
    assert "total_credits_purchased" in data
    assert data["available_credits"] == mock_user["available_credits"]
    assert data["total_credits_purchased"] == mock_user["total_credits_purchased"]

def test_get_credits_packages(mock_services):
    """Test getting credits packages"""
    response = client.get("/credits/packages", headers={"Authorization": "Bearer fake-token"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(mock_packages)
    assert data[0]["id"] == mock_packages[0].id
    assert data[1]["id"] == mock_packages[1].id

def test_create_payment_intent(mock_services, mock_stripe):
    """Test creating a payment intent"""
    response = client.post(
        "/credits/payment-intent",
        headers={"Authorization": "Bearer fake-token"},
        json={"package_id": "basic", "quantity": 1}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "client_secret" in data
    assert data["client_secret"] == "test_secret"
    assert "package" in data
    assert data["package"]["id"] == "basic"

def test_purchase_credits(mock_services):
    """Test purchasing credits"""
    response = client.post(
        "/credits/purchase",
        headers={"Authorization": "Bearer fake-token"},
        json={"payment_intent_id": "pi_test_123456"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "available_credits" in data
    assert "total_credits_purchased" in data
    # No need to verify mocked function calls in this simplified approach

def test_get_stripe_public_key():
    """Test getting Stripe public key"""
    response = client.get("/credits/public-key")
    
    assert response.status_code == 200
    data = response.json()
    assert "publishable_key" in data
    # We don't check the actual key value since it comes from settings 