# backend/ai_client.py
import os
import json
import openai
import logging
from functools import wraps
from cachetools import TTLCache
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
import uuid
from langdetect import detect
from typing import Dict, Any, Optional
import hashlib
from openai import AsyncOpenAI
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

load_dotenv()  # Load environment variables from a .env file

# openai.api_key = os.getenv("OPENAI_API_KEY") # Handled by AsyncOpenAI client

# Removed global ai_cache and related standalone functions

# Set up logging
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
        # Filter prompt_args to only include keys relevant for caching itinerary generation
        # Based on the old standalone generate_cache_key, relevant keys were:
        # "destination", "startDate", "endDate", "travelType", "adults", 
        # "children", "infants", "budgetLevel", "entertainmentPreferences", 
        # "intermediateStops", "cuisinePreference"
        # Assuming trip_request is passed as prompt_args here or a subset of it.
        
        relevant_keys = [
            "destination", "startDate", "endDate", "travelType", "adults",
            "children", "infants", "budgetLevel", "entertainmentPreferences",
            "intermediateStops", "cuisinePreference", "language" # Language also affects output
        ]
        
        key_data = {}
        for key in relevant_keys:
            value = prompt_args.get(key)
            if isinstance(value, list):
                # Sort lists to ensure consistent order for caching
                try:
                    key_data[key] = sorted(value)
                except TypeError: # If list contains un-sortable items like dicts
                    # For lists of dicts (e.g., intermediateStops), sort by a consistent key if possible
                    if key == "intermediateStops" and value and isinstance(value[0], dict):
                         try:
                            key_data[key] = sorted(value, key=lambda x: (x.get('destination',''), x.get('startDate','')))
                         except TypeError:
                            key_data[key] = value # Fallback if sorting dicts fails
                    else:
                        key_data[key] = value 
            else:
                key_data[key] = value
        
        # Convert to a stable string representation
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _log_api_call(self, prompt_args: Dict[str, Any], is_cached: bool):
        """Log API call details"""
        logger.info(
            f"[AI-CALL] {datetime.now().isoformat()} - "
            f"Model: {self.model}, "
            f"Cached: {is_cached}, "
            f"Args: {json.dumps({k: prompt_args.get(k) for k in ['destination', 'startDate', 'endDate', 'language']}, sort_keys=True)[:100]}..."
        )

    def clear_cache_for_request(self, trip_request: Dict[str, Any]):
        """Clear the cache for a specific trip request"""
        key = self._generate_cache_key(trip_request)
        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache cleared for request: {key}")
            return True
        logger.info(f"Cache key {key} not found for clearing.")
        return False

    def is_cached(self, trip_request: Dict[str, Any]):
        """Check if a response for this trip request is already cached"""
        key = self._generate_cache_key(trip_request)
        return key in self.cache

    @ai_model_decorator()
    async def generate_itinerary(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a travel itinerary based on the provided arguments"""
        try:
            # Handle deprecated model names
            if self.model == "gpt-4-turbo-8k": # This specific string check
                logger.warning(f"Model '{self.model}' is deprecated, using '{AI_CONFIG['default_model']}' instead")
                self.model = AI_CONFIG["default_model"]
                
            cache_key = self._generate_cache_key(trip_request)
            
            if cache_key in self.cache:
                self._log_api_call(trip_request, is_cached=True)
                return self.cache[cache_key]
            
            self._log_api_call(trip_request, is_cached=False)
            prompt = self._generate_prompt(trip_request)
            
            logger.info(f"Sending request to OpenAI with model {self.model}")
            logger.debug(f"Prompt structure: { {key: type(val) for key, val in json.loads(prompt).items()} if isinstance(prompt,str) and prompt.startswith('{') else 'String prompt' }")

            try:
                # The prompt from _generate_prompt is a single string, not system/user pair
                # The old call_openai_api took a single prompt string and constructed messages.
                # The AIClient's direct call to completions.create needs messages.
                # Let's adjust to ensure messages are built correctly here or in _generate_prompt
                
                system_content = "You are a travel planning assistant. Create detailed itineraries with specific times and activities. Use the exact format specified in the prompt."
                user_content = prompt # Assuming _generate_prompt returns the user part of the prompt

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ],
                    **get_model_config(self.model) # Use model-specific config
                )
                
                if not response or not response.choices or not response.choices[0].message:
                    raise ValueError("Invalid response structure from OpenAI API")
                    
                logger.info("Received response from OpenAI")
                # logger.debug(f"Raw response: {response}") # Can be very verbose
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty content in response from OpenAI API")
                    
                itinerary = await self._process_response(content, trip_request)
                self.cache[cache_key] = itinerary
                
                return itinerary
                
            except openai.APIError as api_error:
                logger.error(f"OpenAI API error during completions.create: {str(api_error)}")
                raise ValueError(f"OpenAI API error: {str(api_error)}") 
            except Exception as e_api_call:
                logger.error(f"Unexpected error during OpenAI API call: {str(e_api_call)}", exc_info=True)
                raise ValueError(f"Unexpected error during API call: {str(e_api_call)}")
            
        except ValueError as ve:
            logger.error(f"ValueError in generate_itinerary: {str(ve)}", exc_info=True)
            return self._create_fallback_itinerary(trip_request)
        except Exception as e:
            logger.error(f"Error generating itinerary with model {self.model}: {str(e)}", exc_info=True) 
            return self._create_fallback_itinerary(trip_request)

    def _generate_prompt(self, args: Dict[str, Any]) -> str:
        """Generate a prompt for the AI model.
        This prompt is expected to be the 'user' part of the chat messages.
        """
        # Format intermediate stops if they exist
        intermediate_stops_text = ""
        if args.get('intermediateStops') and len(args.get('intermediateStops')) > 0:
            stops = []
            for stop_data in args.get('intermediateStops', []):
                if isinstance(stop_data, dict):
                    stop_text = f"{stop_data.get('destination','N/A')} (arrival: {stop_data.get('startDate','N/A')}, stay: {stop_data.get('days','N/A')} days)"
                    stops.append(stop_text)
                else:
                    stops.append(str(stop_data))

            intermediate_stops_text = (
                f"\n- Intermediate Stops: {', '.join(stops)}. "
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
            elif cuisine_preference in ['seafood', 'mediterranean', 'asian', 'european', 'american', 'mexican', 'japanese', 'italian', 'slavic', 'indian', 'thai', 'other']:
                cuisine_instruction = f"Prioritize {cuisine_preference} restaurants and cafes for meal recommendations. When possible, suggest authentic establishments. "
            else:
                cuisine_instruction = f"Consider {cuisine_preference} cuisine if possible. "

        # Handle language
        language = args.get('language', 'en')
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'ru': 'Russian', 'zh': 'Chinese', 
        }
        output_language = language_names.get(language, 'English')
        
        # Using a more structured way to build prompt, e.g., list of strings then join
        prompt_lines = [
            f"Act as a Travel Planner Assistant. Create a detailed itinerary for a trip from {args.get('startDate')} to {args.get('endDate')}. Provide a full plan for EACH day.",
            "Trip Details:",
            f"- From: {args.get('origin', 'Not specified')}",
            f"- To: {args.get('destination', 'Not specified')}",
            f"- Dates: {args.get('startDate')} to {args.get('endDate')}",
            "- Activities Time: from 9 AM to 6 PM",
            f"- Travel Type: {args.get('travelType', 'leisure')}",
            f"- Number of travelers: {args.get('adults', 1)} adults, {args.get('children', 0)} children, {args.get('infants', 0)} infants",
            f"- Budget Level: {args.get('budgetLevel', 'moderate')}",
            f"- Entertainment Preferences: {', '.join(args.get('entertainmentPreferences', []))}",
            f"- Cuisine: {cuisine_preference}{intermediate_stops_text}",
            "",
            "OUTPUT REQUIREMENTS MUST BE FOLLOWED:",
            "- Use the EXACT format below for each activity.",
            f"- Write ALL content in {output_language.upper()}.",
            f"- YOU MUST PROVIDE FULL DETAILS FOR EVERY SINGLE DAY from {args.get('startDate')} to {args.get('endDate')} inclusive. ",
            "- DO NOT SUMMARIZE. DO NOT SKIP DAYS. The final output MUST contain a [DAY_START]...[DAY_END] block for each date in the range.",
            "",
            "FORMAT:",
            "[DAY_START]",
            "Date: YYYY-MM-DD",
            "[ACTIVITY_START]",
            "Time: HH:MM AM/PM - HH:MM AM/PM",
            "Type: travel|food|activity|sightseeing|accommodation",
            "Description: Detailed activity description",
            "Why: Explanation of why this activity is recommended for the trip requirements",
            "Price: free|$|$$|$$$",
            "Location: Specific place name",
            "Coordinates: latitude,longitude (if available)",
            "[ACTIVITY_END]",
            "... (more activities for the day)",
            "[DAY_END]",
            "",
            "RULES:",
            f"1. Write ALL content in {output_language.upper()} - this includes descriptions, explanations, and location names (except where untranslatable)",
            "2. Start activities no earlier than 9:00 AM and end no later than 7:00 PM",
            f"3. Include lunch breaks between 12:00 PM and 2:00 PM. {cuisine_instruction}Suggest 2-3 specific places based on the requirements and take into account the location of activities before and after lunch break.",
            "4. Each activity should be 1-3 hours long. If the activity involves a tour/entertainment, be more specific and share 2-3 of the most popular companies to choose from, including why they might be chosen.",
            "5. Use the EXACT format shown above (DAY_START, ACTIVITY_START, etc.).",
            "6. Include 3-6 activities per day.",
            "7. If you need to drive more than 3 hours between activities, suggest a 15-30 minute break/activity/sightseeing.",
            "8. For intermediate stops, use the EXACT dates provided - do not modify them. Include appropriate activities for the specified duration at each stop.",
            ("9. Always include a price level for each activity:\\n"
             "    - free: No cost (parks, walking tours, public spaces)\\n"
             "    - $: Low cost (basic museums, casual dining)\\n"
             "    - $$: Moderate cost (guided tours, mid-range restaurants)\\n"
             "    - $$$: High cost (luxury experiences, fine dining)"),
            ("10. For EACH activity, include a required \"Why\" section that explains:\\n"
             "    - How it matches the user's preferences\\n"
             "    - What makes it special or unique\\n"
             "    - Why it's recommended at this specific time/location\\n"
             "    - How it fits with the overall itinerary"),
            "11. If destination is a park or related to a nature or user has chosen \"Outdoor\" activity, suggest a nature activity: trails, hikes, etc.",
            "",
            "Remember to follow all formatting rules above and incorporate the breakdown by date/city."
        ]
        return "\n".join(prompt_lines)

    async def _process_response(self, response: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process the response from the AI model"""
        # Define regex patterns as constants for readability and reuse
        RE_DAY_DATE = re.compile(r'Date: (\d{4}-\d{2}-\d{2})')
        RE_ACTIVITY_BLOCKS = re.compile(r'(\[ACTIVITY_START\].*?(?=\n\s*\[ACTIVITY_START\]|\n\s*\[DAY_END\]|$))', re.DOTALL)
        RE_TIME = re.compile(r'Time:\s*(.+?)\n')
        RE_TYPE = re.compile(r'Type:\s*(travel|food|activity|sightseeing|accommodation|lunch)\s*\n', re.IGNORECASE)
        RE_PRICE = re.compile(r'Price:\s*(free|\$|\$\$|\$\$\$)\s*\n', re.IGNORECASE)
        RE_LOCATION = re.compile(r'Location:\s*(.*?)(?=\n\s*(?:Coordinates:|Why:|Price:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)
        RE_COORDINATES_TEXT = re.compile(r'Coordinates:\s*(.*?)(?=\n\s*(?:Why:|Price:|Location:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)
        RE_DESCRIPTION = re.compile(r'Description:\s*(.*?)(?=\n\s*(?:Why:|Price:|Location:|Coordinates:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)
        RE_WHY = re.compile(r'Why:\s*(.*?)(?=\n\s*(?:Price:|Location:|Coordinates:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)

        # Patterns for parsing coordinates string
        COORDINATE_PATTERNS = [
            re.compile(r'([+-]?\d+\.?\d*)\s*[°]?\s*[NSns]?,?\s*([+-]?\d+\.?\d*)\s*[°]?\s*[EWew]?', re.IGNORECASE),
            re.compile(r'([+-]?\d+\.?\d*)\s*,\s*([+-]?\d+\.?\d*)'),
            re.compile(r'([+-]?\d+\.?\d*)[^\d.,-]+([+-]?\d+\.?\d*)') # More general
        ]

        def parse_coordinates(coords_str: str) -> Optional[Dict[str, float]]:
            if coords_str.lower() in ['n/a', 'not available', '']:
                return None
            for pattern in COORDINATE_PATTERNS:
                match = pattern.search(coords_str)
                if match:
                    try:
                        lat = float(match.group(1))
                        lon = float(match.group(2))
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            return {'latitude': lat, 'longitude': lon}
                    except (ValueError, IndexError, TypeError):
                        continue # Try next pattern
            logger.warning(f"Invalid or unparseable coordinates format: '{coords_str}'")
            return None

        try:
            if not self._validate_response(response, args):
                logger.error("AI response failed validation.")
                raise ValueError("Invalid response format after validation")

            days = []
            raw_days = response.split('[DAY_START]')[1:]

            for day_content in raw_days:
                day_dict = {}
                date_match = RE_DAY_DATE.search(day_content)
                if not date_match:
                    logger.warning("Skipping day block due to missing or invalid date format.")
                    continue
                day_dict['date'] = date_match.group(1)
                
                activities = []
                activity_blocks = RE_ACTIVITY_BLOCKS.findall(day_content)
                
                if not activity_blocks:
                    logger.warning(f"No activities found for date {day_dict['date']}. Skipping day.")
                    continue
                     
                for activity_text_match in activity_blocks:
                    activity_text = activity_text_match if isinstance(activity_text_match, str) else activity_text_match[0]
                    activity_data = {'id': f"{day_dict['date']}-{uuid.uuid4()}"}
                    
                    time_match = RE_TIME.search(activity_text)
                    activity_data['time'] = time_match.group(1).strip() if time_match else "Time not specified"
                    
                    type_match = RE_TYPE.search(activity_text)
                    activity_type_str = type_match.group(1).lower() if type_match else 'activity'
                    activity_data['type'] = 'food' if activity_type_str == 'lunch' else activity_type_str
                    
                    price_match = RE_PRICE.search(activity_text)
                    activity_data['price'] = price_match.group(1) if price_match else '$$'
                    
                    location_match = RE_LOCATION.search(activity_text)
                    activity_data['location'] = location_match.group(1).strip() if location_match else "Location not specified"
                    
                    coords_match_text = RE_COORDINATES_TEXT.search(activity_text)
                    if coords_match_text:
                        parsed_coords = parse_coordinates(coords_match_text.group(1).strip())
                        if parsed_coords:
                            activity_data['coordinates'] = parsed_coords
                    
                    desc_match = RE_DESCRIPTION.search(activity_text)
                    activity_data['description'] = desc_match.group(1).strip() if desc_match else "No description provided."
                    
                    why_match = RE_WHY.search(activity_text)
                    activity_data['why'] = why_match.group(1).strip() if why_match else "Recommended based on travel preferences."
                    
                    activities.append(activity_data)
                
                if activities:
                    day_dict['activities'] = activities
                    days.append(day_dict)

            return {
                'days': days,
                'language': args.get('language', 'en')
            }

        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}", exc_info=True)
            return self._create_fallback_itinerary(args)

    def _validate_response(self, response: str, args: Dict[str, Any]) -> bool:
        """Validate the response format and content.
        Returns True if valid, False otherwise.
        """
        try:
            if not response.strip():
                logger.error("Validation failed: AI response is empty.")
                return False

            required_tags = ['[DAY_START]', '[ACTIVITY_START]']
            if not all(tag in response for tag in required_tags):
                logger.error(f"Validation failed: Missing one or more required tags: {required_tags} in response.")
                return False
            
            if not re.search(r'Date: \d{4}-\d{2}-\d{2}', response):
                logger.error("Validation failed: No valid 'Date: YYYY-MM-DD' found in response.")
                return False

            try:
                target_language = args.get('language', 'en')
                if target_language == 'en':
                    return True

                desc_samples = re.findall(r'Description:\s*(.*?)(?=\n\s*(?:Why:|$))', response, re.DOTALL | re.IGNORECASE)
                sample_text = ' '.join(s.strip() for s in desc_samples if s.strip())[:500]
                
                if sample_text:
                    detected_lang = detect(sample_text)
                    lang_map = {'en': ['en'], 'es': ['es'], 'fr': ['fr'], 'de': ['de'], 'it': ['it'], 'ru': ['ru'], 'zh': ['zh-cn', 'zh-tw']}
                    
                    expected_langs = lang_map.get(target_language, [target_language])
                    if detected_lang not in expected_langs:
                        logger.warning(f"Potential language mismatch. Expected {target_language} (one of {expected_langs}), detected {detected_lang} in sample.")
                # else:
                #     logger.info("No description text found for language validation or target is English.")
            except Exception as lang_e:
                logger.warning(f"Language detection failed during validation: {str(lang_e)}")

            return True

        except Exception as e:
            logger.error(f"Unexpected error during response validation: {str(e)}", exc_info=True)
            return False
            
    def _create_fallback_itinerary(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback itinerary when the AI response cannot be parsed or generation fails"""
        logger.warning(f"Creating fallback itinerary for request to: {trip_data.get('destination', 'Unknown')}")
        try:
            start_date_str = trip_data.get('startDate', datetime.now().strftime('%Y-%m-%d'))
            end_date_str = trip_data.get('endDate', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                logger.error(f"Invalid date format in fallback: {start_date_str} or {end_date_str}. Using defaults.")
                start_date = datetime.now()
                end_date = start_date + timedelta(days=1)

            days_count = (end_date - start_date).days + 1
            
            if days_count <= 0:
                 logger.warning(f"Invalid date range for fallback: {start_date_str} to {end_date_str}. Defaulting to 1 day.")
                 days_count = 1
                 end_date = start_date

            itinerary = {"days": [], "language": trip_data.get('language', 'en')}
            destination = trip_data.get('destination', 'Selected Destination')
            
            for i in range(days_count):
                current_date_obj = start_date + timedelta(days=i)
                current_date_str_fb = current_date_obj.strftime('%Y-%m-%d')
                
                activities = [
                    {
                        "id": str(uuid.uuid4()), "time": "10:00 AM - 12:00 PM", "type": "activity",
                        "description": f"Explore {destination}", "location": destination,
                        "price": "$$", "why": "Default exploration activity."
                    },
                    {
                        "id": str(uuid.uuid4()), "time": "12:30 PM - 2:00 PM", "type": "food",
                        "description": "Lunch at a local spot", "location": "Local Restaurant",
                        "price": "$$", "why": "Enjoy a meal."
                    },
                    {
                        "id": str(uuid.uuid4()), "time": "2:30 PM - 5:30 PM", "type": "sightseeing",
                        "description": "Visit notable attractions", "location": destination,
                        "price": "$$", "why": "Discover local sights."
                    }
                ]
                itinerary["days"].append({"date": current_date_str_fb, "activities": activities})
            
            logger.info(f"Fallback itinerary created successfully with {len(itinerary['days'])} days.")
            return itinerary
        except Exception as e:
             logger.exception(f"Critical error creating fallback itinerary: {str(e)}")
             return {"days": [], "language": trip_data.get('language', 'en'), "error": "Failed to create fallback itinerary due to an internal error."}


# Define what should be exported from this module if it were a library
# For application use, this is less critical but good practice.
__all__ = [
    'AIClient',
]
