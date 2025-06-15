import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from travel_planner_ai.backend.ai_client import AIClient

class TestDistanceFilter:
    """Test distance-based filtering functionality in AI trip generation"""
    
    @pytest.fixture
    def ai_client(self):
        return AIClient(api_key="test_key", provider="openai")
    
    @pytest.fixture
    def base_trip_request(self):
        return {
            "userId": "test_user",
            "destination": "Boston, MA",
            "startDate": "2024-06-01",
            "endDate": "2024-06-05",
            "adults": 2,
            "children": 0,
            "infants": 0,
            "travelType": "road",
            "budgetLevel": "mid-range",
            "language": "en",
            "entertainmentPreferences": ["cultural", "food"],
            "cuisinePreference": "local"
        }
    
    def test_trip_request_without_distance_filter(self, ai_client, base_trip_request):
        """Test that trip requests without origin/distance filter work normally"""
        prompt = ai_client._generate_prompt(base_trip_request)
        
        # Should not contain distance exclusion instructions
        assert "exclusion" not in prompt.lower()
        assert "avoid" not in prompt.lower()
        assert "miles" not in prompt.lower()
        assert "km" not in prompt.lower()
        
        # Should contain normal destination instructions
        assert "Boston, MA" in prompt
        assert "DESTINATION MODE" in prompt
    
    def test_trip_request_with_origin_no_distance_filter(self, ai_client, base_trip_request):
        """Test trip request with origin but no distance filter"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should contain route mode instructions
        assert "ROUTE MODE" in prompt
        assert "New York, NY" in prompt
        assert "Boston, MA" in prompt
        
        # Should not contain distance exclusion instructions
        assert "exclusion" not in prompt.lower()
        assert "avoid activities within" not in prompt.lower()
    
    def test_trip_request_with_distance_filter_miles(self, ai_client, base_trip_request):
        """Test trip request with distance filter in miles"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 75,
            "exclusionUnit": "miles"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should contain route mode instructions
        assert "ROUTE MODE" in prompt
        assert "New York, NY" in prompt
        assert "Boston, MA" in prompt
        
        # Should contain distance exclusion instructions
        assert "75 miles" in prompt
        assert "exclusion" in prompt.lower() or "avoid" in prompt.lower()
        assert "starting location" in prompt.lower() or "origin" in prompt.lower()
    
    def test_trip_request_with_distance_filter_kilometers(self, ai_client, base_trip_request):
        """Test trip request with distance filter in kilometers"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 80,  # Default km value
            "exclusionUnit": "km"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should contain route mode instructions
        assert "ROUTE MODE" in prompt
        assert "New York, NY" in prompt
        
        # Should contain distance exclusion instructions with km
        assert "80 km" in prompt
        assert "exclusion" in prompt.lower() or "avoid" in prompt.lower()
    
    def test_distance_filter_with_different_values(self, ai_client, base_trip_request):
        """Test distance filter with various radius values"""
        test_cases = [
            {"radius": 25, "unit": "miles"},
            {"radius": 100, "unit": "miles"},
            {"radius": 50, "unit": "km"},
            {"radius": 200, "unit": "km"},
        ]
        
        for case in test_cases:
            trip_request = {
                **base_trip_request,
                "origin": "New York, NY",
                "exclusionRadius": case["radius"],
                "exclusionUnit": case["unit"]
            }
            
            prompt = ai_client._generate_prompt(trip_request)
            
            # Should contain the specific distance value
            assert f"{case['radius']} {case['unit']}" in prompt
            assert "exclusion" in prompt.lower() or "avoid" in prompt.lower()
    
    def test_distance_filter_prompt_structure(self, ai_client, base_trip_request):
        """Test that distance filter instructions are properly structured in the prompt"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 50,
            "exclusionUnit": "miles"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should have clear geographic context
        assert "ROUTE MODE" in prompt
        
        # Should have exclusion instructions
        exclusion_instructions = [
            "50 miles",
            "exclusion" in prompt.lower() or "avoid" in prompt.lower(),
            "starting" in prompt.lower() or "origin" in prompt.lower()
        ]
        
        # At least 2 of the 3 exclusion instruction elements should be present
        assert sum(bool(instruction) for instruction in exclusion_instructions) >= 2
    
    def test_distance_filter_with_intermediate_stops(self, ai_client, base_trip_request):
        """Test distance filter works correctly with intermediate stops"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 75,
            "exclusionUnit": "miles",
            "intermediateStops": [
                {"destination": "Hartford, CT", "startDate": "2024-06-02", "days": 1}
            ]
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should contain all location information
        assert "New York, NY" in prompt
        assert "Boston, MA" in prompt
        assert "Hartford, CT" in prompt
        
        # Should contain distance exclusion
        assert "75 miles" in prompt
        assert "exclusion" in prompt.lower() or "avoid" in prompt.lower()
    
    def test_distance_filter_edge_cases(self, ai_client, base_trip_request):
        """Test edge cases for distance filtering"""
        
        # Test with 0 distance (should still work)
        trip_request_zero = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 0,
            "exclusionUnit": "miles"
        }
        
        prompt_zero = ai_client._generate_prompt(trip_request_zero)
        # With the user's change, 0 distance doesn't add exclusion text anymore
        assert "New York, NY" in prompt_zero  # Should still contain origin
        assert "Boston, MA" in prompt_zero    # Should still contain destination
        
        # Test with very large distance
        trip_request_large = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 500,
            "exclusionUnit": "km"
        }
        
        prompt_large = ai_client._generate_prompt(trip_request_large)
        assert "500 km" in prompt_large
    
    def test_distance_filter_without_origin_ignored(self, ai_client, base_trip_request):
        """Test that distance filter is ignored when no origin is provided"""
        trip_request = {
            **base_trip_request,
            # No origin field
            "exclusionRadius": 50,
            "exclusionUnit": "miles"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should not contain distance exclusion instructions
        assert "50 miles" not in prompt
        assert "exclusion" not in prompt.lower()
        
        # Should contain normal destination mode
        assert "DESTINATION MODE" in prompt
    
    def test_distance_filter_with_empty_origin_ignored(self, ai_client, base_trip_request):
        """Test that distance filter is ignored when origin is empty"""
        trip_request = {
            **base_trip_request,
            "origin": "",  # Empty origin
            "exclusionRadius": 50,
            "exclusionUnit": "miles"
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Should not contain distance exclusion instructions
        assert "50 miles" not in prompt
        assert "exclusion" not in prompt.lower()
        
        # Should contain normal destination mode
        assert "DESTINATION MODE" in prompt
    
    @patch('travel_planner_ai.backend.ai_client.AIClient._call_openai_api')
    async def test_distance_filter_integration(self, mock_api_call, ai_client, base_trip_request):
        """Test full integration of distance filtering in trip generation"""
        
        # Mock API response
        mock_response = {
            "days": [
                {
                    "date": "2024-06-01",
                    "activities": [
                        {
                            "time": "9:00 AM",
                            "description": "Visit Freedom Trail in Boston - historic walking route",
                            "type": "cultural",
                            "location": "Boston, MA"
                        }
                    ]
                }
            ]
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 75,
            "exclusionUnit": "miles"
        }
        
        result = await ai_client.generate_itinerary(trip_request)
        
        # Verify the API was called
        mock_api_call.assert_called_once()
        
        # Verify the prompt contained distance filter instructions
        call_args = mock_api_call.call_args
        system_message = call_args[1]['messages'][0]['content']
        user_message = call_args[1]['messages'][1]['content']
        full_prompt = system_message + user_message
        
        assert "75 miles" in full_prompt
        assert ("exclusion" in full_prompt.lower() or "avoid" in full_prompt.lower())
        
        # Verify successful response
        assert result is not None
        assert "days" in result
        assert len(result["days"]) > 0
    
    def test_distance_filter_retry_prompts(self, ai_client, base_trip_request):
        """Test that distance filter instructions are included in retry prompts"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 100,
            "exclusionUnit": "miles"
        }
        
        # Test retry prompt generation
        retry_prompt = ai_client._generate_quality_focused_retry_prompt(trip_request, 1, 5)
        
        # Should contain distance exclusion in retry prompts
        assert "100 miles" in retry_prompt
        assert ("exclusion" in retry_prompt.lower() or "avoid" in retry_prompt.lower())
    
    def test_distance_filter_cache_key_generation(self, ai_client, base_trip_request):
        """Test that distance filter affects cache key generation"""
        
        # Request without distance filter
        request_without_filter = {**base_trip_request}
        key_without = ai_client._generate_cache_key(request_without_filter)
        
        # Request with distance filter
        request_with_filter = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 50,
            "exclusionUnit": "miles"
        }
        key_with = ai_client._generate_cache_key(request_with_filter)
        
        # Cache keys should be different
        assert key_without != key_with
        
        # Requests with different distance values should have different cache keys
        request_different_distance = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 100,
            "exclusionUnit": "miles"
        }
        key_different = ai_client._generate_cache_key(request_different_distance)
        
        assert key_with != key_different
    
    def test_distance_filter_quality_requirements(self, ai_client, base_trip_request):
        """Test that distance filter integrates with quality requirements"""
        trip_request = {
            **base_trip_request,
            "origin": "New York, NY",
            "exclusionRadius": 75,
            "exclusionUnit": "miles"
        }
        
        # Test _build_trip_context method
        trip_context = ai_client._build_trip_context(trip_request)
        
        # Should contain route mode information
        assert "ROUTE MODE" in trip_context['geo_context']
        assert "New York, NY" in trip_context['travel_mode']
        assert "Boston, MA" in trip_context['travel_mode'] 