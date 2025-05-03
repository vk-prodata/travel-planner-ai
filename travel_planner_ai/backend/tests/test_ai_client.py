import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from travel_planner_ai.backend.ai_client import AIClient

@pytest.fixture
def ai_client():
    """Return a test instance of the AIClient with test key and 60 second cache TTL"""
    return AIClient(api_key="test-key", cache_ttl=60)

@pytest.mark.asyncio
async def test_generate_itinerary_caching(ai_client):
    """Test that the generate_itinerary method uses caching correctly"""
    # Setup
    trip_request = {
        "destination": "Paris",
        "startDate": "2023-07-01",
        "endDate": "2023-07-05",
        "travelType": "leisure",
        "adults": 2,
        "children": 0,
        "infants": 0,
        "budgetLevel": "medium",
        "entertainmentPreferences": ["museums", "food"],
    }
    
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """
    [DAY_START]
    Date: 2023-07-01
    [ACTIVITY_START]
    Time: 10:00 AM - 12:00 PM
    Type: activity
    Description: Visit the Louvre Museum
    Why: One of the world's most famous museums
    Price: $$
    Location: Louvre Museum
    Coordinates: 48.8606, 2.3376
    [ACTIVITY_END]
    [DAY_END]
    """
    
    # Create async mock for OpenAI client
    mock_openai = AsyncMock()
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Patch the AsyncOpenAI client used within AIClient
    with patch('openai.AsyncOpenAI', return_value=mock_openai):
        # First call should go to the API
        result1 = await ai_client.generate_itinerary(trip_request)
        
        # Second call with same parameters should use cache
        result2 = await ai_client.generate_itinerary(trip_request)
    
    # Verify the API was only called once
    assert mock_openai.chat.completions.create.call_count == 1
    
    # Verify both results are the same
    assert result1 == result2

@pytest.mark.asyncio
async def test_cache_key_generation(ai_client):
    """Test that the cache key is consistent regardless of argument order"""
    # Two identical requests with fields in different order
    request1 = {
        "destination": "Tokyo",
        "startDate": "2023-08-01",
        "adults": 2,
        "endDate": "2023-08-05",
    }
    
    request2 = {
        "startDate": "2023-08-01",
        "destination": "Tokyo",
        "endDate": "2023-08-05",
        "adults": 2,
    }
    
    # Generate cache keys for both
    key1 = ai_client._generate_cache_key(request1)
    key2 = ai_client._generate_cache_key(request2)
    
    # Keys should be identical
    assert key1 == key2, "Cache keys should be identical regardless of field order" 