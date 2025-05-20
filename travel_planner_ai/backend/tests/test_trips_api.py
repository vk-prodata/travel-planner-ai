import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock
from travel_planner_ai.backend.main import app
from datetime import date, timedelta # Added for date calculations

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
    mock_db.trips_collection.find_one.side_effect = [None, mock_trip] # Adjusted for create
    mock_db.trips_collection.insert_one.return_value = MagicMock(inserted_id="new-trip-id")
    
    with patch("travel_planner_ai.backend.routers.trips.get_db", return_value=mock_db):
        # Patch credit deduction for simplicity in these tests
        with patch("travel_planner_ai.backend.routers.trips.deduct_credits_for_trip", return_value={"available_credits": 10}) as mock_deduct_credits:
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
        "formData": {
            "destination": "Paris",
            "startDate": "2023-06-01",
            "endDate": "2023-06-07", # 6 days duration
            "travelType": "flight",
            "adults": 2,
            "children": 0,
            "infants": 0,
            "budget": "mid-range"
        },
        "itinerary": mock_trip["itinerary"]
    }
    
    # Reset side_effect for this specific test if needed, or ensure default is suitable
    # For this test, we want the first find_one (hash check) to return None.
    # And the second find_one (after insert) to return a mock_trip like structure.
    mock_db_instance = client.app.dependency_overrides[app.dependency_overrides_provider.get_dependency(name='get_db')]() # Get the mock_db instance
    created_trip_mock = {**mock_trip, "_id": "new-trip-id", "id": "new-trip-id"} # Simulate created trip
    mock_db_instance.trips_collection.find_one.side_effect = [None, created_trip_mock]

    response = client.post(
        "/trips",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    
    assert response.status_code == 200, response.text
    created_trip_response = response.json()
    assert created_trip_response["user_id"] == mock_user["id"]
    assert created_trip_response["formData"]["destination"] == "Paris"

def test_create_trip_duration_too_long():
    """Test creating a trip with duration longer than 10 days."""
    start_date = date(2024, 1, 1)
    end_date = start_date + timedelta(days=11) # 11 days duration
    trip_data = {
        "userId": mock_user["id"],
        "formData": {
            "destination": "Long Trip",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "travelType": "flight"
        },
        "itinerary": {} # Minimal itinerary
    }
    response = client.post(
        "/trips",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    assert response.status_code == 422, response.text
    response_data = response.json()
    assert "detail" in response_data
    # Pydantic v2 errors are in a list
    if isinstance(response_data["detail"], list):
        assert any("Trip duration cannot exceed 10 days." in error["msg"] for error in response_data["detail"])
    else: # Older Pydantic or direct FastAPI HTTPException
        assert "Trip duration cannot exceed 10 days." in response_data["detail"]

def test_create_trip_duration_valid_max():
    """Test creating a trip with a valid duration (10 days)."""
    start_date = date(2024, 1, 1)
    end_date = start_date + timedelta(days=10) # 10 days duration
    trip_data = {
        "userId": mock_user["id"],
        "formData": {
            "destination": "Valid Trip",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "travelType": "flight"
        },
        "itinerary": {}
    }
    
    # Ensure mocks are set for successful creation
    mock_db_instance = client.app.dependency_overrides[app.dependency_overrides_provider.get_dependency(name='get_db')]()
    created_trip_mock = {
        **mock_trip, 
        "_id": "valid-trip-id", "id": "valid-trip-id", 
        "formData": trip_data["formData"] # Use the actual form data
    }
    mock_db_instance.trips_collection.find_one.side_effect = [None, created_trip_mock]
    mock_db_instance.trips_collection.insert_one.return_value = MagicMock(inserted_id="valid-trip-id")

    response = client.post(
        "/trips",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    assert response.status_code == 200, response.text
    created_trip_response = response.json()
    assert created_trip_response["formData"]["destination"] == "Valid Trip"

def test_create_trip_end_date_before_start_date():
    """Test creating a trip where end date is before start date."""
    start_date = date(2024, 1, 10)
    end_date = date(2024, 1, 1) # End date before start date
    trip_data = {
        "userId": mock_user["id"],
        "formData": {
            "destination": "Invalid Date Trip",
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "travelType": "flight"
        },
        "itinerary": {}
    }
    response = client.post(
        "/trips",
        headers={"Authorization": "Bearer fake-token"},
        json=trip_data
    )
    assert response.status_code == 422, response.text
    response_data = response.json()
    assert "detail" in response_data
    if isinstance(response_data["detail"], list):
        assert any("End date cannot be earlier than start date." in error["msg"] for error in response_data["detail"])
    else:
        assert "End date cannot be earlier than start date." in response_data["detail"]

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