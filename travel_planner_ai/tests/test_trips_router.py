# tests/test_trips_router.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from bson import ObjectId
import datetime

# Important: We need to patch the auth dependency before importing app
with patch("travel_planner_ai.backend.auth.get_current_user") as mock_auth:
    # Setup auth mock to return a test user
    mock_auth.return_value = {
        "id": "test-user",
        "email": "test@example.com",
        "name": "Test User"
    }
    from travel_planner_ai.backend.main import app

client = TestClient(app)

# Mock MongoDB response
class MockCollection:
    def __init__(self, data=None):
        self.data = data or []
        
    def find(self, query=None):
        # Filter data based on query
        if query and 'user_id' in query:
            return [item for item in self.data if item.get('user_id') == query['user_id']]
        return self.data
        
    def find_one(self, query=None):
        if not query:
            return None
            
        # Check if querying by id
        if 'id' in query:
            for item in self.data:
                if item.get('id') == query['id'] and item.get('user_id') == query['user_id']:
                    return item
        
        # Check if querying by _id
        if '_id' in query:
            for item in self.data:
                if str(item.get('_id')) == str(query['_id']) and item.get('user_id') == query['user_id']:
                    return item
                    
        return None
        
    def insert_one(self, document):
        # Add _id field to simulate MongoDB behavior
        document['_id'] = ObjectId()
        self.data.append(document)
        return MagicMock(inserted_id=document['_id'])
        
    def delete_one(self, query):
        initial_len = len(self.data)
        if 'id' in query:
            self.data = [item for item in self.data if 
                        item.get('id') != query['id'] or 
                        item.get('user_id') != query['user_id']]
        elif '_id' in query:
            self.data = [item for item in self.data if 
                        str(item.get('_id')) != str(query['_id']) or 
                        item.get('user_id') != query['user_id']]
                        
        deleted = initial_len - len(self.data)
        return MagicMock(deleted_count=deleted)


# Mock database dependency
@pytest.fixture
def mock_db():
    # Create a test database with some sample data
    test_trips = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "id": "test-trip-1",
            "user_id": "test-user",
            "formData": {
                "destination": "Paris",
                "startDate": "2024-06-01",
                "endDate": "2024-06-07",
                "travelType": "flight",
                "adults": 2
            },
            "itinerary": {
                "days": [
                    {
                        "date": "2024-06-01",
                        "activities": [
                            {
                                "id": "act1",
                                "time": "09:00 AM",
                                "description": "Arrive in Paris",
                                "type": "travel"
                            }
                        ]
                    }
                ]
            },
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
    ]
    
    mock_collection = MockCollection(test_trips)
    db = MagicMock()
    db.trips_collection = mock_collection
    return db


# Bypass authentication for testing
@pytest.fixture(autouse=True)
def override_dependency(mock_db):
    # Setup our mocks so they're used directly in the test
    with patch("travel_planner_ai.backend.routers.trips.get_db") as mock_get_db:
        # Configure mock to return the mock_db fixture
        mock_get_db.return_value = mock_db
        yield


# Tests
def test_get_user_trips():
    # Make request
    response = client.get("/trips", headers={"Authorization": "Bearer fake_token"})
    
    # Assert response
    assert response.status_code == 200
    trips = response.json()
    assert isinstance(trips, list)
    assert len(trips) == 1
    assert trips[0]["id"] == "test-trip-1"
    assert trips[0]["user_id"] == "test-user"
    assert "itinerary" in trips[0]
    assert "days" in trips[0]["itinerary"]
    # Check for updated_at field
    assert "updated_at" in trips[0]


def test_get_trip_by_id():
    # Make request with the test trip id
    response = client.get("/trips/test-trip-1", headers={"Authorization": "Bearer fake_token"})
    
    # Assert response
    assert response.status_code == 200
    trip = response.json()
    assert trip["id"] == "test-trip-1"
    assert trip["user_id"] == "test-user"
    assert "itinerary" in trip
    assert "days" in trip["itinerary"]
    # Check for updated_at field
    assert "updated_at" in trip


def test_trip_not_found():
    # Make request with a non-existent trip id
    response = client.get("/trips/non-existent", headers={"Authorization": "Bearer fake_token"})
    
    # Assert response
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


def test_create_trip():
    # Create test data
    new_trip = {
        "userId": "test-user",
        "formData": {
            "destination": "Rome",
            "startDate": "2024-07-01",
            "endDate": "2024-07-07",
            "travelType": "flight",
            "adults": 1
        }
    }
    
    # Make request
    response = client.post("/trips", headers={"Authorization": "Bearer fake_token"}, json=new_trip)
    
    # Assert response
    assert response.status_code == 200
    created_trip = response.json()
    assert created_trip["user_id"] == "test-user"
    assert created_trip["formData"]["destination"] == "Rome"
    assert "id" in created_trip
    # Check timestamp fields
    assert "created_at" in created_trip
    assert "updated_at" in created_trip


def test_delete_trip():
    # Make request to delete the test trip
    response = client.delete("/trips/test-trip-1", headers={"Authorization": "Bearer fake_token"})
    
    # Assert response
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "deleted successfully" in result["message"]
    
    # Verify trip is deleted
    get_response = client.get("/trips/test-trip-1", headers={"Authorization": "Bearer fake_token"})
    assert get_response.status_code == 404 