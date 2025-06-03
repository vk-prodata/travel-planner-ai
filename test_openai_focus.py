#!/usr/bin/env python3
"""
Focused OpenAI Test Runner
Run only the 10-day English OpenAI test from the comprehensive test suite.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from travel_planner_ai.backend.ai_client import AIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_openai_10_day_completion():
    """Test OpenAI 10-day completion (Test 1 from comprehensive suite)"""
    print("\n" + "="*60)
    print("🚀 FOCUSED OPENAI 10-DAY COMPLETION TEST")
    print("="*60)
    
    # Test 1: OpenAI 10-day English London trip
    start_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=39)).strftime('%Y-%m-%d')
    
    trip_request = {
        'destination': 'London, UK',
        'startDate': start_date,
        'endDate': end_date,
        'travelType': 'vacation',
        'adults': 2,
        'children': 0,
        'infants': 0,
        'budgetLevel': 'mid-range',
        'entertainmentPreferences': ['culture', 'food', 'sightseeing'],
        'cuisinePreference': 'local',
        'language': 'en',
        'aiProvider': 'openai'
    }
    
    print(f"📍 Testing: {trip_request['destination']}")
    print(f"📅 Dates: {start_date} to {end_date} (10 days)")
    print(f"🤖 Provider: OpenAI")
    print(f"🌍 Language: English")
    print(f"💰 Budget: {trip_request['budgetLevel']}")
    print(f"🎯 Preferences: {', '.join(trip_request['entertainmentPreferences'])}")
    
    try:
        ai_client = AIClient(provider="openai")
        
        print(f"\n⏳ Generating itinerary with {ai_client.provider.upper()} ({ai_client.model})...")
        
        start_time = datetime.now()
        result = await ai_client.generate_itinerary(trip_request)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Validate results
        days_generated = len(result.get('days', []))
        expected_days = 10
        
        print(f"\n📊 RESULTS:")
        print(f"⏱️  Generation time: {duration:.1f} seconds")
        print(f"📅 Days generated: {days_generated}/{expected_days}")
        
        # Token usage analysis
        if 'token_usage' in result:
            token_info = result['token_usage']
            print(f"🪙 Tokens used: {token_info['total_tokens']} total")
            print(f"   • Prompt: {token_info['prompt_tokens']} tokens")
            print(f"   • Completion: {token_info['completion_tokens']} tokens")
            
            utilization = (token_info['total_tokens'] / 16000) * 100  # Assuming 16k limit for OpenAI
            print(f"   • Utilization: {utilization:.1f}%")
        
        # Success/Failure determination
        success = days_generated >= expected_days
        status = "✅ PASS" if success else "❌ FAIL"
        
        print(f"\n🎯 TEST RESULT: {status}")
        
        if not success:
            print(f"❌ COMPLETION FAILURE: Only {days_generated}/{expected_days} days generated")
            print(f"   This indicates the OpenAI completion fix is not working properly.")
        else:
            print(f"✅ COMPLETION SUCCESS: All {days_generated} days generated")
            print(f"   OpenAI completion fix is working correctly!")
        
        # Quality validation
        if days_generated > 0:
            sample_day = result['days'][0]
            activities_count = len(sample_day.get('activities', []))
            print(f"📋 Quality check: Day 1 has {activities_count} activities")
            
            if activities_count > 0:
                sample_activity = sample_day['activities'][0]
                desc_length = len(sample_activity.get('description', ''))
                why_length = len(sample_activity.get('why', ''))
                print(f"   • Description length: {desc_length} chars")
                print(f"   • Why explanation length: {why_length} chars")
                
                if desc_length < 50 or why_length < 30:
                    print(f"   ⚠️  Quality warning: Short descriptions/explanations")
                else:
                    print(f"   ✅ Quality good: Detailed descriptions and explanations")
        
        return success
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False

async def main():
    """Run the focused OpenAI test"""
    print("🦎 Starting Focused OpenAI 10-Day Completion Test")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the test
    success = await test_openai_10_day_completion()
    
    # Final summary
    print("\n" + "="*60)
    print("📋 FINAL TEST SUMMARY")
    print("="*60)
    
    if success:
        print("🎉 SUCCESS: OpenAI 10-day completion test PASSED!")
        print("✅ The completion fixes are working correctly.")
        print("💡 You can now proceed with confidence that OpenAI generates complete itineraries.")
    else:
        print("💥 FAILURE: OpenAI 10-day completion test FAILED!")
        print("❌ The completion fixes need further investigation.")
        print("🔧 Check the logs above for specific issues.")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 