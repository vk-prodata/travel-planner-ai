# backend/ai_client.py
import os
import json
import openai
import logging
from functools import wraps
from cachetools import TTLCache, cached
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import uuid
from langdetect import detect
from functools import wraps
from typing import Dict, Any, Optional
import hashlib
from openai import AsyncOpenAI
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

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
    language = trip_data.get('language', 'en')

    # Format dates for better readability in the prompt
    start_date_obj = datetime.fromisoformat(trip_data['startDate'])
    end_date_obj = datetime.fromisoformat(trip_data['endDate'])
    
    # Calculate duration for the AI
    delta = (end_date_obj - start_date_obj).days + 1  # +1 to make it inclusive
    
    formatted_start = start_date_obj.strftime('%Y-%m-%d')
    formatted_end = end_date_obj.strftime('%Y-%m-%d')
    
    logger.info(f"Generating prompt for trip from {formatted_start} to {formatted_end} ({delta} days)")

    user_prompt = f"""
    Create a detailed travel itinerary in {language} for a trip from {formatted_start} to {formatted_end}. Calculate the total number of days and provide a full plan for EACH day.
    Trip Details:
    - From: {trip_data.get('origin')}
    - To: {trip_data.get('destination')}
    - Dates: {formatted_start} to {formatted_end}
    - Activities Time: from 9 AM to 6 PM
    - Travel Type: {trip_data.get('travelType', 'leisure')}
    - Number of travelers: {trip_data.get('adults')} adults, {trip_data.get('children')} children, {trip_data.get('infants')} infants
    - Budget Level: {trip_data.get('budgetLevel', 'moderate')}
    - Entertainment Preferences: {', '.join(trip_data.get('entertainmentPreferences', []))}
    - Cuisine Preference: {trip_data.get('cuisinePreference', 'any')}
    """.strip()

    if trip_data.get('interests'):
        user_prompt += f"\n- Interests: {', '.join(trip_data['interests'])}"

    if trip_data.get('cuisinePreferences'):
        user_prompt += f"\n- Cuisine preferences: {', '.join(trip_data['cuisinePreferences'])}"

    if trip_data.get('accommodationType'):
        user_prompt += f"\n- Accommodation type: {trip_data['accommodationType']}"

    if trip_data.get('transportation'):
        user_prompt += f"\n- Transportation: {trip_data['transportation']}"

    if trip_data.get('accessibility'):
        user_prompt += f"\n- Accessibility needs: {trip_data['accessibility']}"

    if trip_data.get('intermediateStops'):
        stops = '; '.join([f"{stop['location']} on {stop['date']}" for stop in trip_data['intermediateStops']])
        user_prompt += f"\n\n### INTERMEDIATE STOPS ###\nInclude these locations on the specified dates:\n{stops}"

    user_prompt += f"""
    
    OUTPUT REQUIREMENTS (VERY IMPORTANT):
    - Use the EXACT format below for each activity.
    - Write ALL content in {language.upper()}.
    - YOU MUST PROVIDE FULL DETAILS FOR EVERY SINGLE DAY from {formatted_start} to {formatted_end} inclusive. 
    - DO NOT SUMMARIZE. DO NOT SKIP DAYS. The final output MUST contain a [DAY_START]...[DAY_END] block for each date in the range.

    FORMAT:
    [DAY_START]
    Date: YYYY-MM-DD
    [ACTIVITY_START]
    Time: HH:MM AM/PM - HH:MM AM/PM
    Type: travel|food|activity|sightseeing|accommodation
    Description: Detailed activity description (IN {language.upper()})
    Why: Explanation of why this activity is recommended (IN {language.upper()})
    Price: free|$|$$|$$$
    Location: Specific place name
    Coordinates: latitude,longitude (if available)
    [ACTIVITY_END]
    ... (more activities for the day)
    [DAY_END]

    RULES:
    1. Write ALL content in {language.upper()}.
    2. Generate full, detailed activities for EVERY DAY requested. No summaries.
    3. Start activities no earlier than 9:00 AM.
    4. End activities no later than 7:00 PM.
    5. Include lunch breaks between 12:00 PM and 2:00 PM.
    6. Each activity should be 1-3 hours long.
    7. Use the EXACT format shown above (DAY_START, ACTIVITY_START, etc.).
    8. Include 3-6 activities per day.
    9. For intermediate stops, use the EXACT dates provided.
    10. Always include price levels (free, $, $$, $$$).
    11. Include "Why" sections explaining activity choices based on preferences.
    """

    # Add language instruction if not English
    if language != 'en':
        user_prompt += f"\n\nPlease generate the itinerary in {get_language_name(language)}."

    system_prompt = """
    You are an expert travel planner AI. Your job is to create detailed, personalized travel itineraries based on user preferences.
    
    Follow these requirements strictly:
    1. Include exact dates for each day using YYYY-MM-DD format
    2. Provide real, researched places and attractions
    3. Be specific with restaurant names, not generic like "Local Restaurant"
    4. Include specific foods/dishes for restaurants
    5. Provide accurate coordinates for all locations
    6. Ensure the entire date range requested is covered with no missing days
    7. Follow the required output format precisely with all required tags
    8. Maintain consistent formatting throughout the itinerary
    
    The itinerary should be practical and follow a logical flow throughout each day and the overall trip.
    """

    logger.info(f"Generated prompt for {trip_data['destination']} trip in {language}")
    return system_prompt.strip(), user_prompt

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
    start_date = datetime.strptime(trip_data.get('startDate', '2023-01-01'), '%Y-%m-%d')
    end_date = datetime.strptime(trip_data.get('endDate', '2023-01-03'), '%Y-%m-%d')
    cuisine_preference = trip_data.get('cuisinePreference', 'any')
    
    # Calculate the total days for the trip (inclusive)
    days = (end_date - start_date).days + 1
    logger.info(f"Creating fallback itinerary for {days} days from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
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
    
    # Ensure we generate an itinerary for every day in the date range
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        current_date_str = current_date.strftime('%Y-%m-%d')
        logger.debug(f"Creating activities for day {day+1}/{days}: {current_date_str}")
        
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
    
    logger.info(f"Fallback itinerary created with {len(itinerary['days'])} days")
    return itinerary

def ai_model_decorator(model: str = None):
    """Decorator to specify which model to use for the API call"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            original_model = self.model
            if model:
                self.model = model
            # Remove model from kwargs if present
            kwargs.pop('model', None)
            result = await func(self, *args, **kwargs)
            self.model = original_model
            return result
        return wrapper
    return decorator

class AIClient:
    def __init__(self, api_key: str = None, cache_ttl: int = 3600):
        """
        Initialize the AI client with caching
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either directly or via OPENAI_API_KEY environment variable")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = AI_CONFIG["default_model"] # Use default from config
        self.cache = TTLCache(maxsize=500, ttl=cache_ttl)
        
    def _generate_cache_key(self, prompt_args: Dict[str, Any]) -> str:
        """Generate a unique cache key from the prompt arguments"""
        # Sort the dictionary to ensure consistent hashing
        sorted_args = json.dumps(prompt_args, sort_keys=True)
        return hashlib.sha256(sorted_args.encode()).hexdigest()
    
    def _log_api_call(self, prompt_args: Dict[str, Any], is_cached: bool):
        """Log API call details"""
        logger.info(
            f"[AI-CALL] {datetime.now().isoformat()} - "
            f"Model: {self.model}, "
            f"Cached: {is_cached}, "
            f"Args: {json.dumps(prompt_args, sort_keys=True)[:100]}..."
        )

    def clear_cache_for_request(self, trip_request):
        """Clear the cache for a specific trip request"""
        key = self._generate_cache_key(trip_request)
        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache cleared for request: {key}")
            return True
        return False

    def is_cached(self, trip_request):
        """Check if a response for this trip request is already cached"""
        key = self._generate_cache_key(trip_request)
        return key in self.cache

    @ai_model_decorator()
    async def generate_itinerary(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a travel itinerary based on the provided arguments"""
        try:
            cache_key = self._generate_cache_key(trip_request)
            
            if cache_key in self.cache:
                self._log_api_call(trip_request, is_cached=True)
                return self.cache[cache_key]
            
            prompt = self._generate_prompt(trip_request)
            
            logger.info(f"Sending request to OpenAI with model {self.model}")
            logger.debug(f"Prompt: {prompt}")
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a travel planning assistant. Create detailed itineraries with specific times and activities. Use the exact format specified in the prompt."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    **get_model_config(self.model) # Use model-specific config
                )
                
                if not response or not response.choices or not response.choices[0].message:
                    raise ValueError("Invalid response from OpenAI API")
                    
                logger.info("Received response from OpenAI")
                logger.debug(f"Raw response: {response}")
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from OpenAI API")
                    
                itinerary = await self._process_response(content, trip_request)
                self.cache[cache_key] = itinerary
                self._log_api_call(trip_request, is_cached=False)
                
                return itinerary
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                raise ValueError(f"OpenAI API error: {str(api_error)}") # Keep raising specific error here
            
        except Exception as e:
            logger.error(f"Error generating itinerary with model {self.model}: {str(e)}") # Use error level
            return self._create_fallback_itinerary(trip_request)

    def _generate_prompt(self, args: Dict[str, Any]) -> str:
        """Generate a prompt for the AI model"""
        # Format intermediate stops if they exist
        intermediate_stops_text = ""
        if args.get('intermediateStops') and len(args.get('intermediateStops')) > 0:
            stops = []
            for stop in args.get('intermediateStops'):
                stop_text = f"{stop.get('destination')} (arrival: {stop.get('startDate')}, stay: {stop.get('days')} days)"
                stops.append(stop_text)
            intermediate_stops_text = (
                f"\n- Intermediate Stops: {', '.join(stops)}. " # Added newline for clarity
                "The first Intermediate stop is the first destination."
            )

        # Build cuisine instruction
        cuisine_preference = args.get('cuisinePreference', 'any')
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

        # Handle language
        language = args.get('language', 'en')
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'ru': 'Russian',
            'zh': 'Chinese'
        }
        output_language = language_names.get(language, 'English')
        
        return f"""
    Act as a Travel Planner Assistant. Create a detailed itinerary for a trip from {args.get('startDate')} to {args.get('endDate')}. Provide a full plan for EACH day.
    Trip Details:
    - From: {args.get('origin')}
    - To: {args.get('destination')}
    - Dates: {args.get('startDate')} to {args.get('endDate')}
    - Activities Time: from 9 AM to 6 PM
    - Travel Type: {args.get('travelType')}
    - Number of travelers: {args.get('adults')} adults, {args.get('children')} children, {args.get('infants')} infants
    - Budget Level: {args.get('budgetLevel')}
    - Entertainment Preferences: {', '.join(args.get('entertainmentPreferences', []))}
    - Cuisine: {cuisine_preference}{intermediate_stops_text}

    OUTPUT REQUIREMENTS MUST BE FOLLOWED:
    - Use the EXACT format below for each activity.
    - Write ALL content in {output_language.upper()}.
    - YOU MUST PROVIDE FULL DETAILS FOR EVERY SINGLE DAY from {args.get('startDate')} to {args.get('endDate')} inclusive. 
    - DO NOT SUMMARIZE. DO NOT SKIP DAYS. The final output MUST contain a [DAY_START]...[DAY_END] block for each date in the range.

    FORMAT:
    [DAY_START]
    Date: YYYY-MM-DD
    [ACTIVITY_START]
    Time: HH:MM AM/PM - HH:MM AM/PM
    Type: travel|food|activity|sightseeing|accommodation
    Description: Detailed activity description
    Why: Explanation of why this activity is recommended for the trip requirements
    Price: free|$|$$|$$$
    Location: Specific place name
    Coordinates: latitude,longitude (if available)
    [ACTIVITY_END]
    ... (more activities for the day)
    [DAY_END]

    RULES:
    1. Write ALL content in {output_language.upper()} - this includes descriptions, explanations, and location names (except where untranslatable)
    2. Start activities no earlier than 9:00 AM and end no later than 7:00 PM
    3. Include lunch breaks between 12:00 PM and 2:00 PM. {cuisine_instruction}Suggest 2-3 specific places based on the requirements and take into account the location of activities before and after lunch break.
    4. Each activity should be 1-3 hours long. If the activity involves a tour/entertainment, be more specific and share 2-3 of the most popular companies to choose from, including why they might be chosen.
    5. Use the EXACT format shown above (DAY_START, ACTIVITY_START, etc.).
    6. Include 3-6 activities per day.
    7. If you need to drive more than 3 hours between activities, suggest a 15-30 minute break/activity/sightseeing.
    8. For intermediate stops, use the EXACT dates provided - do not modify them. Include appropriate activities for the specified duration at each stop.
    9. Always include a price level for each activity:
        - free: No cost (parks, walking tours, public spaces)
        - $: Low cost (basic museums, casual dining)
        - $$: Moderate cost (guided tours, mid-range restaurants)
        - $$$: High cost (luxury experiences, fine dining)
    10. For EACH activity, include a required "Why" section that explains:
        - How it matches the user's preferences
        - What makes it special or unique
        - Why it's recommended at this specific time/location
        - How it fits with the overall itinerary
    11. If destination is a park or related to a nature or user has chosen "Outdoor" activity, suggest a nature activity: trails, hikes, etc.

    Remember to follow all formatting rules above and incorporate the breakdown by date/city.
    """

    async def _process_response(self, response: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process the response from the AI model"""
        try:
            # Validate response format and language
            if not self._validate_response(response, args):
                raise ValueError("Invalid response format")

            # Parse the response into days and activities
            days = []
            raw_days = response.split('[DAY_START]')[1:]  # Skip empty first split

            for day in raw_days:
                day_dict = {}
                
                # Extract date
                date_match = re.search(r'Date: (\d{4}-\d{2}-\d{2})', day)
                if not date_match:
                    # Allow processing to continue if a day block is malformed, but log it
                    logger.warning("Skipping day block due to missing or invalid date format.")
                    continue 
                day_dict['date'] = date_match.group(1)
                
                # Parse activities
                activities = []
                # Find activities using regex to handle potential missing [ACTIVITY_END]
                activity_blocks = re.findall(r'(\[ACTIVITY_START\].*?(?=\n\s*\[ACTIVITY_START\]|\n\s*\[DAY_END\]|$))', day, re.DOTALL)
                
                if not activity_blocks:
                     logger.warning(f"No activities found for date {day_dict['date']}. Skipping day.")
                     continue # Skip days with no activities
                     
                for activity_text_match in activity_blocks:
                    # Handle potential tuple return from findall if capture groups were used unintentionally
                    activity_text = activity_text_match if isinstance(activity_text_match, str) else activity_text_match[0]
                    activity_dict = {}
                    
                    # Extract time more robustly
                    time_match = re.search(r'Time:\s*(.+?)\n', activity_text)
                    activity_dict['time'] = time_match.group(1).strip() if time_match else "Time not specified"
                    
                    # Extract type robustly
                    type_match = re.search(r'Type:\s*(travel|food|activity|sightseeing|accommodation|lunch)\s*\n', activity_text, re.IGNORECASE)
                    activity_dict['type'] = 'food' if type_match and type_match.group(1).lower() == 'lunch' else (type_match.group(1) if type_match else 'activity')
                    
                    # Extract price robustly
                    price_match = re.search(r'Price:\s*(free|\$|\$\$|\$\$\$)\s*\n', activity_text, re.IGNORECASE)
                    price = price_match.group(1) if price_match else '$$'  # Default price
                    
                    # Store price 
                    activity_dict['price'] = price
                    
                    # Extract location robustly
                    location_match = re.search(r'Location:\s*(.*?)(?=\n\s*(?:Coordinates:|Why:|Price:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', activity_text, re.DOTALL | re.IGNORECASE)
                    activity_dict['location'] = location_match.group(1).strip() if location_match else "Location not specified"
                    
                    # Extract coordinates robustly
                    coords_text = None
                    coords_match = re.search(r'Coordinates:\s*(.*?)(?=\n\s*(?:Why:|Price:|Location:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', activity_text, re.DOTALL | re.IGNORECASE)
                    if coords_match:
                        coords_text = coords_match.group(1).strip()
                        if coords_text.lower() not in ['n/a', 'not available', '']:
                            patterns = [
                                r'([+-]?\d+\.?\d*)\s*[°]?\s*[NSns]?,?\s*([+-]?\d+\.?\d*)\s*[°]?\s*[EWew]?', 
                                r'([+-]?\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)', 
                                r'([+-]?\d+\.?\d*)[^\d.,-]+([+-]?\d+\.?\d*)'
                            ]
                            valid_coords = False
                            for pattern in patterns:
                                coords = re.search(pattern, coords_text, re.IGNORECASE)
                                if coords:
                                    try:
                                        lat = float(coords.group(1))
                                        lon = float(coords.group(2))
                                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                                            valid_coords = True
                                            activity_dict['coordinates'] = {'latitude': lat, 'longitude': lon}
                                            break
                                    except (ValueError, IndexError, TypeError):
                                        continue
                            if not valid_coords:
                                logger.warning(f"Invalid or unparseable coordinates format: '{coords_text}' for activity on {day_dict['date']}")
                        # else: logger.info(f"Coordinates marked as not available for activity on {day_dict['date']}")
                    
                    # Extract description robustly
                    desc_match = re.search(r'Description:\s*(.*?)(?=\n\s*(?:Why:|Price:|Location:|Coordinates:|Type:|Time:|\[ACTIVITY_END\]|$))', activity_text, re.DOTALL | re.IGNORECASE)
                    activity_dict['description'] = desc_match.group(1).strip() if desc_match else "No description provided."
                    
                    # Extract why robustly
                    why_match = re.search(r'Why:\s*(.*?)(?=\n\s*(?:Price:|Location:|Coordinates:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', activity_text, re.DOTALL | re.IGNORECASE)
                    activity_dict['why'] = why_match.group(1).strip() if why_match else "Recommended based on travel preferences."
                    
                    activity_dict['id'] = f"{day_dict['date']}-{uuid.uuid4()}" # Ensure unique ID
                    
                    activities.append(activity_dict)
                
                if activities: # Only add day if it has activities
                     day_dict['activities'] = activities
                     days.append(day_dict)
                # No else needed, already logged warning if no activities found

            return {
                'days': days,
                'language': args.get('language', 'en')
            }

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return self._create_fallback_itinerary(args)

    def _validate_response(self, response: str, args: Dict[str, Any]) -> bool:
        """Validate the response format and content"""
        try:
            # Check for required format tags
            if not all(tag in response for tag in ['[DAY_START]', '[DAY_END]', '[ACTIVITY_START]', '[ACTIVITY_END]']):
                # Log error but allow processing if basic structure seems present
                if '[DAY_START]' not in response or 'Date:' not in response:
                     logger.error("Missing required format tags [DAY_START] or Date: in response")
                     return False
                else:
                     logger.warning("Response missing some format tags ([DAY_END], [ACTIVITY_START/END]), attempting parse.")

            # Basic Language validation (optional)
            try:
                target_language = args.get('language', 'en')
                # Find description text more reliably
                desc_samples = re.findall(r'Description:\s*(.*?)(?=\n\s*(?:Why:|$))', response, re.DOTALL | re.IGNORECASE)
                sample_text = ' '.join(desc_samples)[:500] # Limit sample size
                if sample_text:
                    detected_lang = detect(sample_text)
                    lang_map = {'en': ['en'], 'es': ['es'], 'fr': ['fr'], 'de': ['de'], 'it': ['it'], 'ru': ['ru'], 'zh': ['zh-cn', 'zh-tw']}
                    if target_language in lang_map and detected_lang not in lang_map[target_language]:
                        logger.warning(f"Potential language mismatch. Expected {target_language}, detected {detected_lang} in sample.")
                # else: logger.info("No description text found for language validation.")
            except Exception as lang_e:
                logger.warning(f"Language detection failed during validation: {str(lang_e)}")

            return True

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
            
    def _create_fallback_itinerary(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback itinerary when the AI response cannot be parsed"""
        logger.warning(f"Creating fallback itinerary for request: {trip_data.get('destination')}") # Log warning
        try:
            start_date_str = trip_data.get('startDate', datetime.now().strftime('%Y-%m-%d'))
            end_date_str = trip_data.get('endDate', (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'))
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            days_count = (end_date - start_date).days + 1
            
            if days_count <= 0:
                 logger.error(f"Invalid date range for fallback: {start_date_str} to {end_date_str}")
                 days_count = 1 # Ensure at least one day
                 start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                 end_date = start_date

            itinerary = {"days": [], "language": trip_data.get('language', 'en')}
            destination = trip_data.get('destination', 'Unknown Destination')
            
            for i in range(days_count):
                current_date = start_date + timedelta(days=i)
                activities = [
                    {
                        "id": str(uuid.uuid4()),
                        "time": "10:00 AM - 12:00 PM",
                        "type": "activity",
                        "description": f"Fallback: Explore {destination}",
                        "location": destination,
                        "price": "$$",
                        "why": "Default fallback activity."
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "time": "12:30 PM - 2:00 PM",
                        "type": "food",
                        "description": "Fallback: Lunch break",
                        "location": "Local Restaurant",
                        "price": "$$",
                        "why": "Time for lunch."
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "time": "2:30 PM - 5:30 PM",
                        "type": "sightseeing",
                        "description": "Fallback: Visit local attractions",
                        "location": destination,
                        "price": "$$",
                        "why": "Default fallback sightseeing."
                    }
                ]
                
                itinerary["days"].append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "activities": activities
                })
            
            logger.info(f"Fallback itinerary created with {len(itinerary['days'])} days.")
            return itinerary
        except Exception as e:
             logger.exception(f"Error creating fallback itinerary: {str(e)}")
             # Ultimate fallback: return minimal structure
             return {"days": [], "language": trip_data.get('language', 'en'), "error": "Failed to create fallback itinerary"}


# Define what should be exported from this module
__all__ = [
    'AIClient',
    'generate_itinerary',
    'generate_cache_key',
    'clear_cache_for_request',
    'is_cached'
]
