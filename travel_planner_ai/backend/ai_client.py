# backend/ai_client.py
import os
import json
import openai
import logging
from functools import wraps
from cachetools import TTLCache, cached
from travel_planner_ai.backend.models import TripRequest
from dotenv import load_dotenv
import re

load_dotenv()  # Load environment variables from a .env file

openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your environment

# Create a TTL cache with a maximum of 500 items and TTL of 24 hours (86400 seconds)
ai_cache = TTLCache(maxsize=500, ttl=86400)

# Set up logging
logger = logging.getLogger(__name__)

def ai_provider_decorator(provider):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if provider == "GPT-4o":
                return func(*args, **kwargs)
            elif provider == "Gemini":
                # TODO: Implement Gemini integration using its SDK or API.
                raise NotImplementedError("Gemini integration not implemented yet")
            else:
                raise ValueError("Unknown AI provider")
        return wrapper
    return decorator

def generate_cache_key(trip_request):
    """
    Generate a unique cache key based on the trip request parameters.
    This ensures that similar requests get the same cached response.
    """
    # Extract only the fields that affect the itinerary generation
    key_data = {
        "destination": trip_request.destination,
        "startDate": trip_request.startDate,
        "endDate": trip_request.endDate,
        "travelType": trip_request.travelType,
        "adults": trip_request.adults,
        "children": trip_request.children,
        "infants": trip_request.infants,
        "budgetLevel": trip_request.budgetLevel,
        "entertainmentPreferences": sorted(trip_request.entertainmentPreferences) if trip_request.entertainmentPreferences else [],
        "intermediateStops": sorted(trip_request.intermediateStops) if trip_request.intermediateStops else []
    }
    
    # Convert to a stable string representation
    return json.dumps(key_data, sort_keys=True)

def clear_cache_for_request(trip_request):
    """
    Clear the cache for a specific trip request.
    Useful when the user wants to regenerate an itinerary.
    """
    key = generate_cache_key(trip_request)
    if key in ai_cache:
        del ai_cache[key]
        logger.info(f"Cache cleared for request: {key}")
        return True
    return False

def is_cached(trip_request):
    """
    Check if a response for this trip request is already cached.
    """
    key = generate_cache_key(trip_request)
    return key in ai_cache

async def generate_itinerary(trip_request_data):
    """
    Generate an itinerary based on the trip request data.
    Uses caching to avoid redundant API calls.
    """
    # Generate cache key
    cache_key = generate_cache_key(trip_request_data)
    
    # Check if response is in cache
    if cache_key in ai_cache:
        logger.info(f"Cache hit for request: {cache_key}")
        return ai_cache[cache_key]
    
    logger.info(f"Cache miss for request: {cache_key}")
    
    # Generate the prompt for the AI
    prompt = generate_ai_prompt(trip_request_data)
    
    try:
        # Call the OpenAI API
        response = await call_openai_api(prompt)
        
        # Parse the response
        itinerary = parse_ai_response(response, trip_request_data)
        
        # Store in cache
        ai_cache[cache_key] = itinerary
        logger.info(f"Stored in cache: {cache_key}")
        
        return itinerary
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        raise

def generate_ai_prompt(trip_data):
    """
    Generate a detailed prompt for the AI based on the trip request data.
    """
    # Extract trip details
    destination = trip_data.get('destination', '')
    start_date = trip_data.get('startDate', '')
    end_date = trip_data.get('endDate', '')
    travel_type = trip_data.get('travelType', '')
    adults = trip_data.get('adults', 1)
    children = trip_data.get('children', 0)
    infants = trip_data.get('infants', 0)
    budget_level = trip_data.get('budgetLevel', 'medium')
    preferences = trip_data.get('entertainmentPreferences', [])
    language = trip_data.get('language', 'en')
    
    # Map language codes to full language names for clearer instructions
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'ru': 'Russian',
        'zh': 'Chinese'
    }
    
    language_name = language_names.get(language, 'English')
    
    # Build the prompt
    prompt = (
        f"Generate a detailed travel itinerary in {language_name} language for a trip to {destination} "
        f"from {start_date} to {end_date}. "
        f"Travel type: {travel_type}. "
        f"Group: {adults} adults, {children} children, {infants} infants. "
        f"Budget level: {budget_level}. "
        f"Entertainment preferences: {', '.join(preferences)}. "
        f"\n\nIMPORTANT: The entire itinerary must be written in {language_name} language. "
        f"For each meal suggestion, provide 2-3 specific restaurant names with a brief description of each. "
        f"For each activity, include specific locations and venues rather than generic suggestions. "
        f"When possible, include the exact name of attractions, parks, museums, etc. "
        f"Format the response as a JSON object with the following structure:\n"
        f"{{\n"
        f"  \"days\": [\n"
        f"    {{\n"
        f"      \"date\": \"YYYY-MM-DD\",\n"
        f"      \"activities\": [\n"
        f"        {{\n"
        f"          \"time\": \"HH:MM AM/PM\",\n"
        f"          \"description\": \"Detailed description in {language_name}\",\n"
        f"          \"type\": \"activity/meal/transport\",\n"
        f"          \"location\": \"Name of the place\",\n"
        f"          \"coordinates\": \"latitude,longitude\" (if available)\n"
        f"        }}\n"
        f"      ]\n"
        f"    }}\n"
        f"  ]\n"
        f"}}"
    )
    
    return prompt

async def call_openai_api(prompt):
    """
    Call the OpenAI API with the given prompt.
    """
    try:
        # Extract language from prompt for system message
        language_match = re.search(r"in (\w+) language", prompt)
        language = language_match.group(1) if language_match else "English"
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert travel planner. Always provide specific restaurant names and activity locations rather than generic suggestions. Generate all content in {language} language as requested by the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise

def parse_ai_response(response_text, trip_data):
    """
    Parse the AI response into a structured itinerary.
    """
    try:
        # Try to parse the response as JSON
        itinerary = json.loads(response_text)
        
        # Validate the structure
        if not itinerary.get('days'):
            raise ValueError("Invalid response format: 'days' field missing")
        
        # Ensure each day has the required fields
        for day in itinerary['days']:
            if not day.get('date'):
                day['date'] = "Unknown date"
            
            if not day.get('activities'):
                day['activities'] = []
            
            # Ensure each activity has the required fields
            for activity in day['activities']:
                if not activity.get('time'):
                    activity['time'] = "9:00 AM"
                if not activity.get('description'):
                    activity['description'] = "No description available"
                if not activity.get('type'):
                    activity['type'] = "activity"
                if not activity.get('id'):
                    import uuid
                    activity['id'] = str(uuid.uuid4())
        
        return itinerary
    except json.JSONDecodeError:
        logger.error("Failed to parse AI response as JSON")
        # Fallback to a simple structure
        return create_fallback_itinerary(trip_data)
    except Exception as e:
        logger.error(f"Error parsing AI response: {str(e)}")
        return create_fallback_itinerary(trip_data)

def create_fallback_itinerary(trip_data):
    """
    Create a fallback itinerary when the AI response cannot be parsed.
    """
    from datetime import datetime, timedelta
    import uuid
    
    start_date = datetime.strptime(trip_data.get('startDate', '2023-01-01'), '%Y-%m-%d')
    end_date = datetime.strptime(trip_data.get('endDate', '2023-01-03'), '%Y-%m-%d')
    
    days = (end_date - start_date).days + 1
    itinerary = {"days": []}
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        itinerary["days"].append({
            "date": current_date.strftime('%Y-%m-%d'),
            "activities": [
                {
                    "id": str(uuid.uuid4()),
                    "time": "09:00 AM",
                    "description": "Explore local attractions",
                    "type": "activity"
                },
                {
                    "id": str(uuid.uuid4()),
                    "time": "12:00 PM",
                    "description": "Lunch at a local restaurant",
                    "type": "meal"
                },
                {
                    "id": str(uuid.uuid4()),
                    "time": "03:00 PM",
                    "description": "Visit a museum or park",
                    "type": "activity"
                },
                {
                    "id": str(uuid.uuid4()),
                    "time": "07:00 PM",
                    "description": "Dinner at a recommended restaurant",
                    "type": "meal"
                }
            ]
        })
    
    return itinerary
