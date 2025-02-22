import pytest
from unittest.mock import Mock, patch
from travel_planner_ai.backend.ai.base_client import BaseAIClient

@pytest.fixture
def ai_client():
    return BaseAIClient(api_key="test-key", cache_ttl=60)

@pytest.fixture
def mock_openai_response():
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="Day 1: Visit the Eiffel Tower..."))
    ]
    return mock_response

def test_cache_key_generation(ai_client):
    args1 = {"destination": "Paris", "days": 3}
    args2 = {"days": 3, "destination": "Paris"}
    
    # Same content in different order should generate same key
    assert ai_client._generate_cache_key(args1) == ai_client._generate_cache_key(args2)

@patch('openai.OpenAI')
def test_generate_itinerary_caching(mock_openai, ai_client, mock_openai_response):
    # Setup mock
    mock_openai.return_value.chat.completions.create.return_value = mock_openai_response
    
    # Test arguments
    prompt_args = {
        "destination": "Paris",
        "startDate": "2024-03-01",
        "endDate": "2024-03-05",
        "adults": 2,
        "children": 0,
        "budgetLevel": "mid-range"
    }
    
    # First call should hit the API
    result1 = ai_client.generate_itinerary(prompt_args)
    assert mock_openai.return_value.chat.completions.create.called
    
    # Second call should use cache
    mock_openai.reset_mock()
    result2 = ai_client.generate_itinerary(prompt_args)
    assert not mock_openai.return_value.chat.completions.create.called
    
    # Results should be identical
    assert result1 == result2 