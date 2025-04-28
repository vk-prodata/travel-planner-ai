from functools import wraps
from typing import Dict, Any, Optional
from cachetools import TTLCache
import hashlib
import json
import logging
from openai import AsyncOpenAI
from datetime import datetime
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config
import uuid
import re
from langdetect import detect

logger = logging.getLogger(__name__)

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

class BaseAIClient:
    def __init__(self, api_key: str, cache_ttl: int = 3600):
        """
        Initialize the AI client with caching
        
        Args:
            api_key: OpenAI API key
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = AI_CONFIG["default_model"]  # Use the model from config
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        
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

    @ai_model_decorator()
    async def generate_itinerary(self, prompt_args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a travel itinerary based on the provided arguments"""
        try:
            cache_key = self._generate_cache_key(prompt_args)
            
            if cache_key in self.cache:
                self._log_api_call(prompt_args, is_cached=True)
                return self.cache[cache_key]
            
            prompt = self._generate_prompt(prompt_args)
            
            logger.info(f"Sending request to OpenAI with model {self.model}")
            logger.debug(f"Prompt: {prompt}")
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a travel planning assistant. Create detailed itineraries with specific times and activities. Always use the exact format specified in the prompt."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    **get_model_config(self.model)
                )
                
                if not response or not response.choices or not response.choices[0].message:
                    raise ValueError("Invalid response from OpenAI API")
                    
                logger.info("Received response from OpenAI")
                logger.debug(f"Raw response: {response}")
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from OpenAI API")
                    
                itinerary = await self._process_response(content, prompt_args)
                self.cache[cache_key] = itinerary
                self._log_api_call(prompt_args, is_cached=False)
                
                return itinerary
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                raise ValueError(f"OpenAI API error: {str(api_error)}")
            
        except Exception as e:
            logger.error(f"Error generating itinerary with model {self.model}: {str(e)}")
            raise

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
                f"- Intermediate Stops: {', '.join(stops)}. "
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
    Create a detailed travel itinerary in {output_language} with the following requirements:
    - From: {args.get('origin')}
    - To: {args.get('destination')}
    - Dates: {args.get('startDate')} to {args.get('endDate')}
    - Activities Time: from 9 AM to 6 PM
    - Travel Type: {args.get('travelType')}
    - Number of travelers: {args.get('adults')} adults, {args.get('children')} children, {args.get('infants')} infants
    - Budget Level: {args.get('budgetLevel')}
    - Entertainment Preferences: {', '.join(args.get('entertainmentPreferences', []))}
    - Cuisine Preference: {cuisine_preference}
    {intermediate_stops_text}

    IMPORTANT: Use this EXACT format for each activity AND WRITE ALL CONTENT IN {output_language.upper()}:
    [DAY_START]
    Date: YYYY-MM-DD
    [ACTIVITY_START]
    Time: HH:MM AM/PM - HH:MM AM/PM
    Type: travel|food|activity|sightseeing|accommodation
    Description: Detailed activity description (IN {output_language.upper()})
    Why: Explanation of why this activity is recommended (IN {output_language.upper()})
    Price: free|$|$$|$$$
    Location: Specific place name
    Coordinates: latitude,longitude (if available)
    [ACTIVITY_END]
    [DAY_END]

    Example in {output_language}:
    [DAY_START]
    Date: 2025-02-22
    [ACTIVITY_START]
    Time: 9:00 AM - 10:30 AM
    Type: activity
    Description: Visit the City Museum's Ancient Civilizations Exhibition
    Why: Perfect for cultural enthusiasts, featuring interactive displays and rare artifacts. Great for families with children due to the hands-on learning experiences.
    Price: $$
    Location: City Museum
    Coordinates: 12.345,-67.890
    [ACTIVITY_END]
    [DAY_END]

    RULES:
    1. Write ALL content in {output_language.upper()} - this includes descriptions, explanations, and location names (except where untranslatable)
    2. Start activities no earlier than 9:00 AM
    3. End activities no later than 7:00 PM
    4. Include lunch breaks between 12:00 PM and 2:00 PM. {cuisine_instruction}Suggest 2-3 specific places based on the requirements and take into account the location of activities before and after lunch break.
    5. Each activity should be 1-3 hours long. If the activity involves a tour/entertainment, be more specific and share 2-3 of the most popular companies to choose from, including why they might be chosen.
    6. Use the EXACT format shown above (DAY_START, ACTIVITY_START, etc.).
    7. Include 3-6 activities per day.
    8. If you need to drive more than 3 hours between activities, suggest a 15-30 minute break/activity/sightseeing.
    9. For intermediate stops, use the EXACT dates provided - do not modify them. Include appropriate activities for the specified duration at each stop.
    10. Always include a price level for each activity:
        - free: No cost (parks, walking tours, public spaces)
        - $: Low cost (basic museums, casual dining)
        - $$: Moderate cost (guided tours, mid-range restaurants)
        - $$$: High cost (luxury experiences, fine dining)
    11. For EACH activity, include a required "Why" section that explains:
        - How it matches the user's preferences
        - What makes it special or unique
        - Why it's recommended at this specific time/location
        - How it fits with the overall itinerary

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
                    raise ValueError("Missing or invalid date format")
                day_dict['date'] = date_match.group(1)
                
                # Parse activities
                activities = []
                raw_activities = day.split('[ACTIVITY_START]')[1:]
                
                for activity in raw_activities:
                    activity_dict = {}
                    
                    # Extract time
                    time_match = re.search(r'Time: (\d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M)', activity)
                    if not time_match:
                        raise ValueError("Missing or invalid time format")
                    activity_dict['time'] = time_match.group(1)
                    
                    # Extract type
                    type_match = re.search(r'Type: (travel|food|activity|sightseeing|accommodation|lunch)', activity)
                    if not type_match:
                        raise ValueError("Missing or invalid activity type")
                    activity_dict['type'] = 'food' if type_match.group(1) == 'lunch' else type_match.group(1)
                    
                    # Extract price
                    price_match = re.search(r'Price: (free|\$|\$\$|\$\$\$)', activity)
                    if not price_match:
                        raise ValueError("Missing or invalid price format")
                    activity_dict['price'] = price_match.group(1)
                    
                    # Extract location
                    location_match = re.search(r'Location: (.*?)(?=\n|$)', activity)
                    if not location_match:
                        raise ValueError("Missing location")
                    activity_dict['location'] = location_match.group(1).strip()
                    
                    # Extract coordinates if present
                    coords_match = re.search(r'Coordinates: ([+-]?\d+\.?\d*)[°]?\s*[NS]?,\s*([+-]?\d+\.?\d*)[°]?\s*[EW]?', activity)
                    if coords_match:
                        lat = float(coords_match.group(1))
                        lon = float(coords_match.group(2))
                        activity_dict['coordinates'] = {
                            'latitude': lat,
                            'longitude': lon
                        }
                    
                    # Extract description and why section
                    desc_match = re.search(r'Description: (.*?)(?=\nWhy:|$)', activity, re.DOTALL)
                    why_match = re.search(r'Why: (.*?)(?=\nPrice:|$)', activity, re.DOTALL)
                    
                    if not desc_match:
                        raise ValueError("Missing description")
                        
                    description = desc_match.group(1).strip()
                    activity_dict['description'] = description
                    
                    # Always ensure there's a why field, with a fallback if missing
                    if why_match:
                        activity_dict['why'] = why_match.group(1).strip()
                    else:
                        # Provide a fallback "why" message if none is provided by the AI
                        logger.warning(f"Missing 'Why' section for activity at {activity_dict['time']}. Using fallback.")
                        activity_dict['why'] = "This activity complements your itinerary and matches your travel preferences."
                    
                    # Generate a unique ID for the activity
                    activity_dict['id'] = f"{day_dict['date']}-{id(activity_dict)}"
                    
                    activities.append(activity_dict)
                
                day_dict['activities'] = activities
                days.append(day_dict)

            return {
                'days': days,
                'language': args.get('language', 'en')
            }

        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise ValueError(f"Failed to process response: {str(e)}")

    def _validate_response(self, response: str, args: Dict[str, Any]) -> bool:
        """Validate the response format and content"""
        try:
            # Check for required format tags
            if not all(tag in response for tag in ['[DAY_START]', '[DAY_END]', '[ACTIVITY_START]', '[ACTIVITY_END]']):
                logger.error("Missing required format tags in response")
                return False

            # Split into days
            days = response.split('[DAY_START]')[1:]
            if not days:
                logger.error("No days found in response")
                return False

            # Language validation
            target_language = args.get('language', 'en')
            
            # Sample text for language detection (combine descriptions)
            descriptions = re.findall(r'Description: (.*?)(?=\[|$)', response, re.DOTALL)
            if not descriptions:
                logger.error("No descriptions found for language validation")
                return False
            
            sample_text = ' '.join(desc.strip() for desc in descriptions)
            detected_lang = detect(sample_text)
            
            # Map ISO 639-1 codes to our supported languages
            lang_map = {
                'en': ['en'],
                'es': ['es'],
                'fr': ['fr'],
                'de': ['de'],
                'it': ['it'],
                'pt': ['pt'],
                'ru': ['ru'],
                'zh': ['zh-cn', 'zh-tw'],
                'ja': ['ja'],
                'ko': ['ko']
            }
            
            if target_language not in lang_map or detected_lang not in lang_map[target_language]:
                logger.error(f"Language mismatch. Expected {target_language}, detected {detected_lang}")
                return False

            for day in days:
                # Validate date format
                if not re.search(r'Date: \d{4}-\d{2}-\d{2}', day):
                    logger.error("Invalid date format")
                    return False

                # Check for activities
                activities = day.split('[ACTIVITY_START]')[1:]
                if not activities:
                    logger.error("No activities found in day")
                    return False

                for activity in activities:
                    # Validate time format
                    if not re.search(r'Time: \d{1,2}:\d{2} [AP]M - \d{1,2}:\d{2} [AP]M', activity):
                        logger.error("Invalid time format")
                        return False

                    # Validate activity type
                    type_match = re.search(r'Type: (travel|food|activity|sightseeing|accommodation|lunch)', activity)
                    if not type_match:
                        logger.error("Invalid activity type")
                        return False

                    # Validate price format
                    if not re.search(r'Price: (free|\$|\$\$|\$\$\$)', activity):
                        logger.error("Invalid price format")
                        return False

                    # Validate location presence
                    if not re.search(r'Location: .+', activity):
                        logger.error("Missing location")
                        return False

                    # Validate Why section presence
                    if not re.search(r'Why: .+', activity):
                        logger.error("Missing 'Why' section")
                        return False

                    # Validate coordinates format if present
                    coords_match = re.search(r'Coordinates: .+', activity)
                    if coords_match:
                        # Allow both decimal format and degree format
                        valid_coords = re.search(
                            r'Coordinates: ([+-]?\d+\.?\d*)[°]?\s*[NS]?,\s*([+-]?\d+\.?\d*)[°]?\s*[EW]?',
                            activity
                        )
                        if not valid_coords:
                            logger.error("Invalid coordinates format")
                            return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False 