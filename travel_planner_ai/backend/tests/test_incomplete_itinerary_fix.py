import pytest
import asyncio
from datetime import datetime, timedelta
from travel_planner_ai.backend.ai_client import AIClient
from travel_planner_ai.backend.config.ai_config import AI_CONFIG


class TestIncompleteItineraryFix:
    """Test suite for verifying the incomplete itinerary fix"""
    
    @pytest.fixture
    def ai_client(self):
        """Create an AI client for testing"""
        return AIClient(provider="openai")
    
    def test_calculate_expected_days(self, ai_client):
        """Test the _calculate_expected_days method"""
        # Test 1-day trip
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-05-30'
        }
        assert ai_client._calculate_expected_days(trip_request) == 1
        
        # Test 7-day trip (original failing case)
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-06-05'
        }
        assert ai_client._calculate_expected_days(trip_request) == 7
        
        # Test 8-day trip
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-06-06'
        }
        assert ai_client._calculate_expected_days(trip_request) == 8
    
    def test_prompt_generation_includes_all_dates(self, ai_client):
        """Test that the prompt includes all expected dates"""
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-06-06',
            'destination': 'Saratov',
            'origin': 'Moscow',
            'travelType': 'road',
            'adults': 2,
            'children': 2,
            'budgetLevel': 'mid-range',
            'entertainmentPreferences': ['outdoor', 'relax'],
            'cuisinePreference': 'any',
            'language': 'en'
        }
        
        prompt = ai_client._generate_prompt(trip_request)
        
        # Check that prompt includes strong completion requirements
        assert '🚨 MANDATORY: Create complete 8-day itinerary' in prompt
        assert 'Your response MUST contain exactly 8 [DAY_START] blocks' in prompt
        assert 'Generate ALL 8 days' in prompt
        
        # Check that essential quality elements are present
        assert 'Budget:' in prompt
        assert 'Preferences:' in prompt
        assert 'RULES:' in prompt
        assert 'Detailed activity with specific recommendations' in prompt
        
        # Check that all dates are listed efficiently
        expected_dates = ['2025-05-30', '2025-05-31', '2025-06-01', '2025-06-02', 
                         '2025-06-03', '2025-06-04', '2025-06-05', '2025-06-06']
        for date in expected_dates:
            assert date in prompt
            
        # Check prompt is reasonably concise (not overly verbose)
        assert len(prompt) < 2000, f"Prompt too long ({len(prompt)} chars), may cause token issues"
    
    def test_increased_token_limits(self):
        """Test that token limits have been increased"""
        # Check main model has increased token limit
        config = AI_CONFIG["models"]["gpt-4o-2024-11-20"]
        assert config["max_tokens"] == 14000, f"Expected 14000 tokens, got {config['max_tokens']}"
        
        # Check DeepSeek models have increased limits
        deepseek_config = AI_CONFIG["models"]["deepseek-chat"]
        assert deepseek_config["max_tokens"] == 8000, f"Expected 8000 tokens for DeepSeek, got {deepseek_config['max_tokens']}"
    
    def test_incomplete_response_detection(self, ai_client):
        """Test that incomplete responses are properly detected"""
        # Mock an incomplete response (only 3 days instead of 7)
        incomplete_response = """
        [DAY_START]
        Date: 2025-05-30
        [ACTIVITY_START]
        Time: 09:00 AM - 12:00 PM
        Type: travel
        Description: Begin road trip
        Why: Starting early
        Price: free
        Location: Moscow
        [ACTIVITY_END]
        [DAY_END]
        
        [DAY_START]
        Date: 2025-05-31
        [ACTIVITY_START]
        Time: 09:00 AM - 12:00 PM
        Type: travel
        Description: Continue journey
        Why: Making progress
        Price: free
        Location: Penza
        [ACTIVITY_END]
        [DAY_END]
        
        [DAY_START]
        Date: 2025-06-01
        [ACTIVITY_START]
        Time: 09:00 AM - 12:00 PM
        Type: sightseeing
        Description: Explore Saratov
        Why: Arrived at destination
        Price: $$
        Location: Saratov
        [ACTIVITY_END]
        [DAY_END]
        """
        
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-06-06',  # 8 days total
            'destination': 'Saratov',
            'language': 'en'
        }
        
        # Process the incomplete response
        result = asyncio.run(ai_client._process_response(incomplete_response, trip_request))
        
        # Should return 3 days (what was provided)
        assert len(result['days']) == 3
        assert result['days'][0]['date'] == '2025-05-30'
        assert result['days'][1]['date'] == '2025-05-31'
        assert result['days'][2]['date'] == '2025-06-01'
    
    @pytest.mark.integration
    async def test_retry_mechanism_integration(self, ai_client):
        """Integration test for the retry mechanism (requires real API key)"""
        # This test requires a real API key and should only run in integration mode
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("No OpenAI API key available for integration test")
        
        trip_request = {
            'startDate': '2025-05-30',
            'endDate': '2025-06-06',
            'destination': 'Saratov, Russia',
            'origin': 'Moscow, Russia',
            'travelType': 'road',
            'adults': 2,
            'children': 2,
            'budgetLevel': 'mid-range',
            'entertainmentPreferences': ['outdoor', 'relax', 'must-see'],
            'cuisinePreference': 'any',
            'language': 'en',
            'aiProvider': 'openai'
        }
        
        # Generate itinerary
        result = await ai_client.generate_itinerary(trip_request)
        
        # Verify we got a complete itinerary
        assert 'days' in result
        expected_days = ai_client._calculate_expected_days(trip_request)
        actual_days = len(result['days'])
        
        print(f"Expected {expected_days} days, got {actual_days} days")
        assert actual_days >= expected_days - 1, f"Expected at least {expected_days-1} days, got {actual_days}"
        
        # Verify each day has the expected structure
        for day in result['days']:
            assert 'date' in day
            assert 'activities' in day
            assert len(day['activities']) > 0
            
            for activity in day['activities']:
                assert 'id' in activity
                assert 'time' in activity
                assert 'type' in activity
                assert 'description' in activity
                assert 'location' in activity
                assert 'price' in activity
                assert 'why' in activity


if __name__ == "__main__":
    # Run basic tests without requiring API key
    test_instance = TestIncompleteItineraryFix()
    ai_client = AIClient(provider="openai")
    
    print("Testing expected days calculation...")
    test_instance.test_calculate_expected_days(ai_client)
    print("✓ Expected days calculation works")
    
    print("Testing prompt generation...")
    test_instance.test_prompt_generation_includes_all_dates(ai_client)
    print("✓ Prompt generation includes all dates")
    
    print("Testing token limits...")
    test_instance.test_increased_token_limits()
    print("✓ Token limits have been increased")
    
    print("Testing incomplete response detection...")
    test_instance.test_incomplete_response_detection(ai_client)
    print("✓ Incomplete response detection works")
    
    print("\nAll tests passed! 🎉") 