# tests/test_routes.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture
def sample_trip_request():
    return {
        "trip_details": {
            "travel_type": "road_trip",
            "departure": "City A",
            "destination": "City B",
            "start_date": "2023-12-01",
            "end_date": "2023-12-05",
            "num_adults": 2,
            "num_children": 1,
            "num_infants": 0,
            "intermediate_stops": ["City X", "City Y"]
        },
        "preferences": {
            "outdoor": True,
            "cultural": False,
            "relaxation": True,
            "family_friendly": True,
            "food_tours": False
        },
        "budget": {
            "level": "budget"
        },
        "ai_model": {
            "model": "GPT-4o"
        },
        "language": "en"
    }

def test_generate_trip(sample_trip_request):
    response = client.post("/api/generate-trip", json=sample_trip_request)
    assert response.status_code == 200
    data = response.json()
    assert "trip_id" in data
    assert "itinerary" in data
    assert "generated_at" in data

def test_fetch_trip_not_found():
    response = client.get("/api/trip/nonexistent_id")
    assert response.status_code == 404
