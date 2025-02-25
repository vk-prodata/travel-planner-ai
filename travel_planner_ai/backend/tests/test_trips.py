from fastapi.testclient import TestClient
from travel_planner_ai.backend.main import app
from travel_planner_ai.backend.database import get_db
from bson import ObjectId
import pytest
from unittest.mock import MagicMock, patch
import httpx

# Create test client - simplest way
client = TestClient(app)

# Mock data with your actual user info
MOCK_USER = {
    "id": "108452827088915947426",
    "email": "vkusa87@gmail.com",
    "name": "Irina Kudriavtceva"
}

MOCK_TRIPS = [
    {
        "_id": ObjectId("67baa99ee57bbd0a348360a8"),
        "user_id": "108452827088915947426",
        "formData": {
            "travelType": "flight",
            "origin": "tampa",
            "destination": "sarasota",
            "startDate": "2025-02-23",
            "endDate": "2025-02-24",
            "adults": 1,
            "children": 0,
            "infants": 0,
            "intermediateStops": [],
            "entertainmentPreferences": [],
            "budget": "mid-range",
            "budgetLevel": "mid-range",
            "language": "en"
        },
        "trip_hash": "62a2465b459c493849efccf679dd11821a10004101837262a59ed4fe17e22ba6",
        "itinerary": {}
    },
    {
        "_id": ObjectId("67bbb9a87c8334f65707eee9"),
        "user_id": "108452827088915947426",
        "formData": {
            "travelType": "flight",
            "origin": "miami",
            "destination": "orlando",
            "startDate": "2025-04-20",
            "endDate": "2025-02-21",
            "adults": 2,
            "children": 2,
            "infants": 0,
            "intermediateStops": [],
            "entertainmentPreferences": [],
            "budgetLevel": "mid-range",
            "budget": "mid-range",
            "language": "en"
        },
        "trip_hash": "e4372b80cf5eba0dfe9eae662dbb3fc5f3757977dd44c99e675a937c6856dfde",
        "itinerary": {
            "days": []
        }
    }
]

@pytest.fixture
def mock_db():
    """Create a mock database"""
    db = MagicMock()
    db.trips_collection = MagicMock()
    return db

@pytest.fixture
def mock_auth():
    """Mock the authentication to bypass the token validation"""
    # Create a function that will replace the dependency
    async def override_get_current_user():
        return MOCK_USER
        
    # Import the actual dependency
    from travel_planner_ai.backend.auth import get_current_user as actual_get_current_user
        
    # Override the dependency in the app
    app.dependency_overrides[actual_get_current_user] = override_get_current_user
    
    yield
    
    # Clean up after the test
    app.dependency_overrides = {}

def test_get_user_trips_success(mock_db, mock_auth):
    """Test successful retrieval of user trips"""
    # Setup mock database response
    mock_db.trips_collection.find.return_value = MOCK_TRIPS
    
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Make request to the correct endpoint with user_id
    response = client.get(f"/api/trips/user/{MOCK_USER['id']}")
    
    # Verify response
    assert response.status_code == 200
    trips = response.json()
    assert len(trips) == 2
    
    # Verify first trip (Sarasota)
    assert trips[0]["user_id"] == MOCK_USER["id"]
    assert trips[0]["id"] == str(MOCK_TRIPS[0]["_id"])
    assert trips[0]["formData"]["destination"] == "sarasota"
    assert trips[0]["itinerary"] == {}  # Empty dictionary for itinerary
    
    # Verify second trip (Orlando)
    assert trips[1]["formData"]["destination"] == "orlando"
    assert trips[1]["itinerary"] == {"days": []}  # Existing itinerary preserved

def test_get_user_trips_unauthenticated():
    """Test trips retrieval without authentication"""
    # Remove auth override to test unauthenticated request
    app.dependency_overrides = {}
    
    # Without valid auth, this should return 403 Forbidden
    response = client.get(f"/api/trips/user/{MOCK_USER['id']}")
    assert response.status_code == 403  # API returns 403 Forbidden instead of 401

def test_get_user_trips_database_error(mock_db, mock_auth):
    """Test handling database errors"""
    # Setup mock to raise exception
    mock_db.trips_collection.find.side_effect = Exception("Database error")
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Make request
    response = client.get(f"/api/trips/user/{MOCK_USER['id']}")
    
    # Verify error response
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

# Clean up after tests
def teardown_module(module):
    app.dependency_overrides.clear() 