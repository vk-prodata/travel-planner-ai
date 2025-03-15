import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock
from travel_planner_ai.backend.main import app

client = TestClient(app)

# Mock user for authentication
mock_user = {
    "id": "test-user-id",
    "email": "test@example.com",
    "name": "Test User"
}

# Mock trip data
mock_trip = {
    "id": "test-trip-id",
    "_id": "test-trip-id",
    "user_id": "test-user-id",
    "formData": {
        "destination": "Paris",
        "startDate": "2023-06-01",
        "endDate": "2023-06-07",
        "travelType": "flight",
        "adults": 2,
        "children": 0,
        "infants": 0,
        "budget": "mid-range"
    },
    "itinerary": {
        "tripId": "test-trip-id",
        "days": [
            {
                "date": "2023-06-01",
                "activities": [
                    {
                        "id": "activity-1",
                        "time": "09:00",
                        "description": "Arrive at Charles de Gaulle Airport",
                        "type": "travel"
                    }
                ]
            }
        ]
    },
    "created_at": "2023-05-15T12:00:00",
    "updated_at": "2023-05-15T12:00:00"
}

# Mock the authentication dependency
@pytest.fixture(autouse=True)
def mock_auth():
    with patch("travel_planner_ai.backend.routers.trips.get_current_user", return_value=mock_user):
        yield

# Mock the database dependency
@pytest.fixture(autouse=True)
def mock_db():
    mock_db = MagicMock()
    mock_db.trips_collection.find.return_value = [mock_trip]
    mock_db.trips_collection.find_one.return_value = mock_trip
    
    with patch("travel_planner_ai.backend.routers.trips.get_db", return_value=mock_db):
        yield mock_db

def test_get_user_trips():
    """Test getting all trips for a user"""
    # Mock a trip without an itinerary field to test the fix
    mock_db = MagicMock()
    mock_db.trips_collection.find.return_value = [
        {
            "_id": "test-trip-id-1",
            "user_id": mock_user["id"],
            "formData": mock_trip["formData"],
            "created_at": "2023-05-15T12:00:00",
            "updated_at": "2023-05-15T12:00:00"
        },
        {
            "_id": "test-trip-id-2",
            "user_id": mock_user["id"],
            "formData": mock_trip["formData"],
            "itinerary": mock_trip["itinerary"],
            "created_at": "2023-05-15T12:00:00",
            "updated_at": "2023-05-15T12:00:00"
        }
    ]
    
    with patch("travel_planner_ai.backend.routes.get_db", return_value=mock_db):
        response = client.get(
            f"/trips/user/{mock_user['id']}",
            headers={"Authorization": "Bearer fake-token"}
        )
    
    assert response.status_code == 200
    trips = response.json()
    assert isinstance(trips, list)
    assert len(trips) == 2
    
    # Check that both trips have the itinerary field
    for trip in trips:
        assert "itinerary" in trip
        assert trip["user_id"] == mock_user["id"]
    
    # First trip should have an empty itinerary that was added by our fix
    assert trips[0]["itinerary"]["days"] == []
    
    # Second trip should have the original itinerary
    assert trips[1]["itinerary"] == mock_trip["itinerary"]

def test_get_trip_by_id():
    """Test getting a specific trip by ID"""
    response = client.get(
        f"/trips/{mock_trip['id']}",
        headers={"Authorization": "Bearer fake-token"}
    )
    
    assert response.status_code == 200
    trip = response.json()
    assert trip["id"] == mock_trip["id"]
    assert trip["user_id"] == mock_user["id"]

def test_create_trip():
    """Test creating a new trip"""
    trip_data = {
        "userId": mock_user["id"],
        "formData": mock_trip["formData"],
        "itinerary": mock_trip["itinerary"]
    }
    
    response = client.post(
        "/trips",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    
    assert response.status_code == 200
    created_trip = response.json()
    assert created_trip["user_id"] == mock_user["id"]
    assert created_trip["formData"]["destination"] == mock_trip["formData"]["destination"]

def test_update_trip():
    """Test updating an existing trip"""
    trip_data = {
        "userId": mock_user["id"],
        "formData": {
            **mock_trip["formData"],
            "destination": "Updated Destination"
        },
        "itinerary": mock_trip["itinerary"]
    }
    
    response = client.put(
        f"/trips/{mock_trip['id']}",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    
    assert response.status_code == 200
    updated_trip = response.json()
    assert updated_trip["formData"]["destination"] == "Updated Destination"

def test_delete_trip():
    """Test deleting a trip"""
    response = client.delete(
        f"/trips/{mock_trip['id']}",
        headers={"Authorization": "Bearer fake-token"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "deleted" in result["message"].lower() 