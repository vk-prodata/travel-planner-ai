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
        "intermediateStops": sorted(trip_request.intermediateStops) if trip_request.intermediateStops else [],
        "cuisinePreference": trip_request.cuisinePreference
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
    cuisine_preference = trip_data.get('cuisinePreference', 'any')
    
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

    # Build cuisine instruction based on preference
    cuisine_instruction = ""
    if cuisine_preference != 'any':
        if cuisine_preference == 'local':
            cuisine_instruction = "Focus on authentic local and traditional restaurants of the region. "
        elif cuisine_preference in ['vegetarian', 'vegan', 'halal', 'kosher']:
            cuisine_instruction = f"Only suggest {cuisine_preference} restaurants and cafes. Ensure all meal recommendations comply with {cuisine_preference} dietary requirements. "
        elif cuisine_preference == 'international':
            cuisine_instruction = "Suggest a diverse mix of international restaurants representing various world cuisines. "
        elif cuisine_preference in ['seafood', 'mediterranean', 'asian', 'european', 'american', 'mexican', 'japanese', 'italian', 'slavic', 'indian', 'thai']:
            cuisine_instruction = f"Prioritize {cuisine_preference} restaurants and cafes for meal recommendations. When possible, suggest authentic establishments. "
    
    # Build the prompt
    prompt = (
        f"Generate a detailed travel itinerary in {language_name} language for a trip to {destination} "
        f"from {start_date} to {end_date}. "
        f"Travel type: {travel_type}. "
        f"Group: {adults} adults, {children} children, {infants} infants. "
        f"Budget level: {budget_level}. "
        f"Entertainment preferences: {', '.join(preferences)}. "
        f"\n\nIMPORTANT: The entire itinerary must be written in {language_name} language. "
        f"{cuisine_instruction}"
        f"For each meal suggestion, provide 2-3 specific restaurant names with a brief description of each, including their signature dishes or specialties. "
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
        
        # Extract cuisine preference from prompt
        cuisine_patterns = [
            r"Focus on authentic local",
            r"Only suggest (vegetarian|vegan|halal|kosher)",
            r"Suggest a diverse mix of international",
            r"Prioritize (seafood|mediterranean|asian|european|american|mexican|japanese|italian|slavic|indian|thai)"
        ]
        
        cuisine_instruction = ""
        for pattern in cuisine_patterns:
            match = re.search(pattern, prompt)
            if match:
                if match.groups():
                    cuisine_type = match.group(1)
                    if cuisine_type in ['vegetarian', 'vegan', 'halal', 'kosher']:
                        cuisine_instruction = f" Ensure all restaurant recommendations are certified {cuisine_type}."
                    else:
                        cuisine_instruction = f" Focus on authentic {cuisine_type} cuisine."
                else:
                    cuisine_instruction = " Focus on authentic local cuisine."
                break
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert travel planner and culinary guide with deep knowledge of global cuisines and restaurants. Always provide specific restaurant names and activity locations rather than generic suggestions.{cuisine_instruction} Include signature dishes and specialties when recommending restaurants. Generate all content in {language} language as requested by the user."},
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
    cuisine_preference = trip_data.get('cuisinePreference', 'any')
    
    days = (end_date - start_date).days + 1
    itinerary = {"days": []}
    
    # Process intermediate stops if available
    intermediate_stops = {}
    if trip_data.get('intermediateStops'):
        for stop in trip_data.get('intermediateStops'):
            if stop.get('startDate') and stop.get('days') and stop.get('destination'):
                stop_date = datetime.strptime(stop.get('startDate'), '%Y-%m-%d')
                stop_days = int(stop.get('days'))
                
                # Create a dictionary of dates to stop information
                for i in range(stop_days):
                    current_date = (stop_date + timedelta(days=i)).strftime('%Y-%m-%d')
                    intermediate_stops[current_date] = stop.get('destination')
    
    def get_meal_description(meal_type, location):
        """Generate meal description based on cuisine preference"""
        if cuisine_preference == 'any':
            return f"{meal_type} at a local restaurant in {location}"
        elif cuisine_preference == 'local':
            return f"{meal_type} at a traditional local restaurant in {location}"
        elif cuisine_preference == 'international':
            return f"{meal_type} at an international cuisine restaurant in {location}"
        elif cuisine_preference in ['vegetarian', 'vegan', 'halal', 'kosher']:
            return f"{meal_type} at a certified {cuisine_preference} restaurant in {location}"
        else:
            cuisine_display = {
                'seafood': 'fresh seafood',
                'mediterranean': 'Mediterranean',
                'asian': 'Asian',
                'european': 'European',
                'american': 'American',
                'mexican': 'Mexican',
                'japanese': 'Japanese',
                'italian': 'Italian',
                'slavic': 'Slavic',
                'indian': 'Indian',
                'thai': 'Thai'
            }.get(cuisine_preference, cuisine_preference)
            return f"{meal_type} at an authentic {cuisine_display} restaurant in {location}"
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        current_date_str = current_date.strftime('%Y-%m-%d')
        
        # Check if this day is at an intermediate stop
        location = trip_data.get('destination')
        is_intermediate_stop = False
        
        if current_date_str in intermediate_stops:
            location = intermediate_stops[current_date_str]
            is_intermediate_stop = True
        
        day_activities = []
        
        # If it's the first day and there's an origin, add travel activity
        if day == 0 and trip_data.get('origin'):
            day_activities.append({
                "id": str(uuid.uuid4()),
                "time": "09:00 AM",
                "description": f"Travel from {trip_data.get('origin')} to {location}",
                "type": "travel"
            })
        
        # If it's an intermediate stop's first day, add arrival activity
        elif is_intermediate_stop and current_date_str == datetime.strptime(
            next((s.get('startDate') for s in trip_data.get('intermediateStops', []) 
                 if s.get('destination') == location), 
                current_date_str), 
            '%Y-%m-%d').strftime('%Y-%m-%d'):
            day_activities.append({
                "id": str(uuid.uuid4()),
                "time": "09:00 AM",
                "description": f"Arrive at {location}",
                "type": "travel"
            })
        
        # Add standard activities
        day_activities.extend([
            {
                "id": str(uuid.uuid4()),
                "time": "10:00 AM",
                "description": f"Explore {location} attractions",
                "type": "activity"
            },
            {
                "id": str(uuid.uuid4()),
                "time": "12:00 PM",
                "description": get_meal_description("Lunch", location),
                "type": "meal"
            },
            {
                "id": str(uuid.uuid4()),
                "time": "03:00 PM",
                "description": f"Visit a museum or park in {location}",
                "type": "activity"
            },
            {
                "id": str(uuid.uuid4()),
                "time": "07:00 PM",
                "description": get_meal_description("Dinner", location),
                "type": "meal"
            }
        ])
        
        itinerary["days"].append({
            "date": current_date_str,
            "activities": day_activities
        })
    
    return itinerary
