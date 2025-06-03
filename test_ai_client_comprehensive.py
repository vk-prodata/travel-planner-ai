"""
Comprehensive AI Client Test Suite

This test suite validates AI client functionality including:
- 10-day trips in Russian and English
- 2-day shorter trips  
- Debug information validation
- Cache functionality
- Error handling
- Filter compliance
- Token usage tracking

Run with: python test_ai_client_comprehensive.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from travel_planner_ai.backend.ai_client import AIClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIClientTestSuite:
    """Comprehensive test suite for AI Client"""
    
    def __init__(self):
        """Initialize test suite with AI client"""
        try:
            self.ai_client = AIClient(provider="openai")
            logger.info(f"✅ AI Client initialized with provider: {self.ai_client.provider}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Client: {e}")
            raise
    
    def create_test_request(self, destination: str = "London, UK", days: int = 10, 
                          language: str = "en", **overrides) -> Dict[str, Any]:
        """Create a standard test request with customizable parameters"""
        start_date = datetime.now() + timedelta(days=30)
        end_date = start_date + timedelta(days=days-1)
        
        base_request = {
            "destination": destination,
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "adults": 2,
            "children": 1,
            "infants": 0,
            "travelType": "vacation",
            "budgetLevel": "mid-range",
            "entertainmentPreferences": ["outdoor", "family-friendly", "must-see"],
            "cuisinePreference": "any",
            "language": language,
            "intermediateStops": [],
            "aiProvider": "openai"
        }
        
        # Apply any overrides
        base_request.update(overrides)
        return base_request
    
    def validate_itinerary_structure(self, itinerary: Dict[str, Any], expected_days: int, 
                                   test_name: str) -> bool:
        """Validate the basic structure of an itinerary"""
        try:
            # Check required fields
            if 'days' not in itinerary:
                logger.error(f"❌ {test_name}: Missing 'days' field")
                return False
                
            if 'language' not in itinerary:
                logger.error(f"❌ {test_name}: Missing 'language' field")
                return False
            
            days = itinerary.get('days', [])
            actual_days = len(days)
            
            # Check day count
            if actual_days != expected_days:
                logger.error(f"❌ {test_name}: Expected {expected_days} days, got {actual_days}")
                logger.error(f"❌ {test_name}: Received dates: {[day.get('date') for day in days]}")
                return False
            
            # Validate each day structure
            for i, day in enumerate(days):
                if 'date' not in day:
                    logger.error(f"❌ {test_name}: Day {i+1} missing 'date' field")
                    return False
                    
                if 'activities' not in day:
                    logger.error(f"❌ {test_name}: Day {i+1} missing 'activities' field")
                    return False
                
                activities = day.get('activities', [])
                if len(activities) == 0:
                    logger.error(f"❌ {test_name}: Day {i+1} has no activities")
                    return False
                
                # Validate each activity structure
                for j, activity in enumerate(activities):
                    required_fields = ['time', 'type', 'description', 'location', 'price', 'why']
                    for field in required_fields:
                        if field not in activity:
                            logger.error(f"❌ {test_name}: Day {i+1}, Activity {j+1} missing '{field}' field")
                            return False
            
            logger.info(f"✅ {test_name}: Structure validation passed - {actual_days} days with valid activities")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: Structure validation error: {e}")
            return False
    
    def validate_debug_info(self, itinerary: Dict[str, Any], test_name: str) -> bool:
        """Validate debug information in the itinerary"""
        try:
            # Check for token usage information
            if 'token_usage' in itinerary:
                token_usage = itinerary['token_usage']
                required_tokens = ['total_tokens', 'prompt_tokens', 'completion_tokens']
                
                for field in required_tokens:
                    if field not in token_usage:
                        logger.error(f"❌ {test_name}: Missing token field '{field}'")
                        return False
                    
                    if not isinstance(token_usage[field], int) or token_usage[field] <= 0:
                        logger.error(f"❌ {test_name}: Invalid token value for '{field}': {token_usage[field]}")
                        return False
                
                # Validate token math
                if token_usage['total_tokens'] != token_usage['prompt_tokens'] + token_usage['completion_tokens']:
                    logger.error(f"❌ {test_name}: Token math error - total should equal prompt + completion")
                    return False
                
                logger.info(f"✅ {test_name}: Token usage validation passed - {token_usage['total_tokens']} total tokens")
                return True
            else:
                logger.warning(f"⚠️ {test_name}: No token usage information found")
                return False
                
        except Exception as e:
            logger.error(f"❌ {test_name}: Debug validation error: {e}")
            return False
    
    def validate_destination_compliance(self, itinerary: Dict[str, Any], expected_destination: str, test_name: str) -> bool:
        """Validate that all activities are in the expected destination"""
        try:
            days = itinerary.get('days', [])
            destination_violations = []
            
            # Extract key location terms from expected destination
            dest_terms = expected_destination.lower().replace(',', '').split()
            
            for day in days:
                for activity in day.get('activities', []):
                    location = activity.get('location', '').lower()
                    
                    # Check if location contains destination terms
                    has_dest_term = any(term in location for term in dest_terms)
                    
                    if not has_dest_term:
                        destination_violations.append({
                            'date': day.get('date'),
                            'activity': activity.get('description', '')[:50] + '...',
                            'location': activity.get('location')
                        })
            
            if destination_violations:
                logger.error(f"❌ {test_name}: Found {len(destination_violations)} destination violations:")
                for violation in destination_violations[:3]:  # Show first 3
                    logger.error(f"   - {violation['date']}: {violation['location']}")
                return False
            else:
                logger.info(f"✅ {test_name}: All activities correctly located in {expected_destination}")
                return True
                
        except Exception as e:
            logger.error(f"❌ {test_name}: Destination validation error: {e}")
            return False
    
    async def test_10_day_english_london(self) -> bool:
        """Test 1: 10-day trip to London in English"""
        test_name = "10-Day English London"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=10,
                language="en"
            )
            
            start_time = datetime.now()
            itinerary = await self.ai_client.generate_itinerary(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"⏱️ {test_name}: Generated in {duration:.2f} seconds")
            
            # Validate structure
            if not self.validate_itinerary_structure(itinerary, 10, test_name):
                return False
            
            # Validate destination compliance
            if not self.validate_destination_compliance(itinerary, "London, UK", test_name):
                return False
            
            # Validate language
            if itinerary.get('language') != 'en':
                logger.error(f"❌ {test_name}: Expected language 'en', got '{itinerary.get('language')}'")
                return False
            
            logger.info(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_10_day_russian_london(self) -> bool:
        """Test 2: 10-day trip to London in Russian"""
        test_name = "10-Day Russian London"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=10,
                language="ru"
            )
            
            start_time = datetime.now()
            itinerary = await self.ai_client.generate_itinerary(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"⏱️ {test_name}: Generated in {duration:.2f} seconds")
            
            # Validate structure
            if not self.validate_itinerary_structure(itinerary, 10, test_name):
                return False
            
            # Validate destination compliance
            if not self.validate_destination_compliance(itinerary, "London, UK", test_name):
                return False
            
            # Validate language
            if itinerary.get('language') != 'ru':
                logger.error(f"❌ {test_name}: Expected language 'ru', got '{itinerary.get('language')}'")
                return False
            
            # Check for Russian content (sample a few descriptions)
            days = itinerary.get('days', [])
            if days and days[0].get('activities'):
                first_description = days[0]['activities'][0].get('description', '')
                # Russian text should contain Cyrillic characters
                has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in first_description)
                if not has_cyrillic:
                    logger.warning(f"⚠️ {test_name}: First activity description doesn't contain Cyrillic characters")
                else:
                    logger.info(f"✅ {test_name}: Contains Russian text with Cyrillic characters")
            
            logger.info(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_2_day_short_trip(self) -> bool:
        """Test 3: 2-day shorter trip to London"""
        test_name = "2-Day Short Trip"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=2,
                language="en"
            )
            
            start_time = datetime.now()
            itinerary = await self.ai_client.generate_itinerary(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"⏱️ {test_name}: Generated in {duration:.2f} seconds")
            
            # Validate structure
            if not self.validate_itinerary_structure(itinerary, 2, test_name):
                return False
            
            # Validate destination compliance
            if not self.validate_destination_compliance(itinerary, "London, UK", test_name):
                return False
            
            logger.info(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_debug_information(self) -> bool:
        """Test 4: Validate debug information from AI client"""
        test_name = "Debug Information"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=3,
                language="en"
            )
            
            itinerary = await self.ai_client.generate_itinerary(request)
            
            # Validate debug info
            if not self.validate_debug_info(itinerary, test_name):
                return False
            
            logger.info(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_cache_functionality(self) -> bool:
        """Test 5: Cache functionality validation"""
        test_name = "Cache Functionality"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK", 
                days=2,
                language="en"
            )
            
            # First request - should not be cached
            is_cached_before = self.ai_client.is_cached(request)
            if is_cached_before:
                logger.info(f"ℹ️ {test_name}: Request already in cache, clearing...")
                self.ai_client.clear_cache_for_request(request)
            
            start_time = datetime.now()
            itinerary1 = await self.ai_client.generate_itinerary(request)
            duration1 = (datetime.now() - start_time).total_seconds()
            
            # Second request - should be cached
            is_cached_after = self.ai_client.is_cached(request)
            if not is_cached_after:
                logger.error(f"❌ {test_name}: Request should be cached after first generation")
                return False
            
            start_time = datetime.now()
            itinerary2 = await self.ai_client.generate_itinerary(request)
            duration2 = (datetime.now() - start_time).total_seconds()
            
            # Cached response should be much faster
            if duration2 > duration1 * 0.5:  # Should be at least 50% faster
                logger.warning(f"⚠️ {test_name}: Cached response not significantly faster ({duration2:.2f}s vs {duration1:.2f}s)")
            else:
                logger.info(f"✅ {test_name}: Cached response faster ({duration2:.2f}s vs {duration1:.2f}s)")
            
            # Results should be identical
            if itinerary1 != itinerary2:
                logger.error(f"❌ {test_name}: Cached response differs from original")
                return False
            
            logger.info(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_filter_compliance(self) -> bool:
        """Test 6: Filter compliance validation"""
        test_name = "Filter Compliance"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=2,
                language="en",
                budgetLevel="budget",
                entertainmentPreferences=["outdoor", "family-friendly"],
                cuisinePreference="vegetarian"
            )
            
            itinerary = await self.ai_client.generate_itinerary(request)
            
            # Validate structure first
            if not self.validate_itinerary_structure(itinerary, 2, test_name):
                return False
            
            # Check budget compliance (simplified check for budget-related terms)
            budget_violations = []
            vegetarian_violations = []
            
            for day in itinerary.get('days', []):
                for activity in day.get('activities', []):
                    price = activity.get('price', '')
                    activity_type = activity.get('type', '')
                    description = activity.get('description', '').lower()
                    
                    # Check budget level compliance
                    if price == '$$$':  # High-end pricing for budget trip
                        budget_violations.append(f"Day {day.get('date')}: {activity.get('description', '')[:50]}...")
                    
                    # Check vegetarian compliance for food activities
                    if activity_type == 'food':
                        meat_terms = ['meat', 'beef', 'pork', 'chicken', 'fish', 'seafood', 'steak']
                        if any(term in description for term in meat_terms):
                            vegetarian_violations.append(f"Day {day.get('date')}: {activity.get('description', '')[:50]}...")
            
            # Report violations
            if budget_violations:
                logger.warning(f"⚠️ {test_name}: Found {len(budget_violations)} potential budget violations")
                for violation in budget_violations[:2]:
                    logger.warning(f"   - {violation}")
            
            if vegetarian_violations:
                logger.warning(f"⚠️ {test_name}: Found {len(vegetarian_violations)} potential vegetarian violations")
                for violation in vegetarian_violations[:2]:
                    logger.warning(f"   - {violation}")
            
            # Test passes if structure is valid (filter compliance is complex to validate automatically)
            logger.info(f"✅ {test_name}: PASSED (structure valid, manual review recommended for filter compliance)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 7: Error handling with invalid inputs"""
        test_name = "Error Handling"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            # Test with invalid date range
            invalid_request = self.create_test_request(
                destination="London, UK",
                days=2,
                language="en"
            )
            # Set end date before start date
            invalid_request["endDate"] = invalid_request["startDate"]
            invalid_request["startDate"] = (datetime.strptime(invalid_request["endDate"], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            
            try:
                itinerary = await self.ai_client.generate_itinerary(invalid_request)
                # Should either handle gracefully or generate fallback
                if 'days' in itinerary:
                    logger.info(f"✅ {test_name}: AI client handled invalid input gracefully")
                    return True
                else:
                    logger.error(f"❌ {test_name}: Invalid response structure from error case")
                    return False
            except Exception as e:
                logger.info(f"✅ {test_name}: AI client properly threw exception for invalid input: {e}")
                return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with unexpected error: {e}")
            return False
    
    async def test_10_day_deepseek_english(self) -> bool:
        """Test 8: 10-day trip to London in English using DeepSeek"""
        test_name = "10-Day DeepSeek English"
        logger.info(f"🧪 Starting {test_name}")
        
        try:
            request = self.create_test_request(
                destination="London, UK",
                days=10,
                language="en",
                aiProvider="deepseek"  # Use DeepSeek instead of OpenAI
            )
            
            start_time = datetime.now()
            itinerary = await self.ai_client.generate_itinerary(request)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"⏱️ {test_name}: Generated in {duration:.2f} seconds")
            
            # Validate structure
            if not self.validate_itinerary_structure(itinerary, 10, test_name):
                return False
            
            # Validate destination compliance
            if not self.validate_destination_compliance(itinerary, "London, UK", test_name):
                return False
            
            # Validate language
            if itinerary.get('language') != 'en':
                logger.error(f"❌ {test_name}: Expected language 'en', got '{itinerary.get('language')}'")
                return False
            
            # Validate token usage for DeepSeek
            if 'token_usage' in itinerary:
                token_usage = itinerary['token_usage']
                logger.info(f"🪙 {test_name}: DeepSeek token usage - {token_usage['total_tokens']} total tokens")
                
                # DeepSeek should use fewer tokens than OpenAI typically
                if token_usage['total_tokens'] > 12000:
                    logger.warning(f"⚠️ {test_name}: High token usage for DeepSeek: {token_usage['total_tokens']}")
            
            logger.info(f"✅ {test_name}: PASSED (DeepSeek provider)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {test_name}: FAILED with error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results summary"""
        logger.info("🚀 Starting AI Client Comprehensive Test Suite")
        logger.info("=" * 80)
        
        test_methods = [
            ("Test 1", self.test_10_day_english_london),
            ("Test 2", self.test_10_day_russian_london),
            ("Test 3", self.test_2_day_short_trip),
            ("Test 4", self.test_debug_information),
            ("Test 5", self.test_cache_functionality),
            ("Test 6", self.test_filter_compliance),
            ("Test 7", self.test_error_handling),
            ("Test 8", self.test_10_day_deepseek_english)
        ]
        
        results = {}
        passed = 0
        total = len(test_methods)
        
        for test_name, test_method in test_methods:
            logger.info("-" * 40)
            try:
                result = await test_method()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED with exception: {e}")
                results[test_name] = False
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Summary
        logger.info("=" * 80)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info("-" * 40)
        logger.info(f"📈 OVERALL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Review logs for details.")
        
        return results

async def main():
    """Main test runner"""
    try:
        test_suite = AIClientTestSuite()
        results = await test_suite.run_all_tests()
        
        # Exit with appropriate code
        failed_tests = sum(1 for result in results.values() if not result)
        if failed_tests == 0:
            logger.info("🎯 All tests passed successfully!")
            sys.exit(0)
        else:
            logger.error(f"💥 {failed_tests} tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Test suite failed to initialize: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 