from functools import wraps
from typing import Dict, Any, Optional
from cachetools import TTLCache
import hashlib
import json
import logging
from openai import AsyncOpenAI
from datetime import datetime
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

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
            
            prompt = self._build_itinerary_prompt(prompt_args)
            
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
                    
                itinerary = self._parse_itinerary_response(content)
                self.cache[cache_key] = itinerary
                self._log_api_call(prompt_args, is_cached=False)
                
                return itinerary
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                raise ValueError(f"OpenAI API error: {str(api_error)}")
            
        except Exception as e:
            logger.error(f"Error generating itinerary with model {self.model}: {str(e)}")
            raise

    def _build_itinerary_prompt(self, args: Dict[str, Any]) -> str:
        return f"""
        Create a detailed travel itinerary with the following requirements:
        - From: {args.get('origin')}
        - To: {args.get('destination')}
        - Dates: {args.get('startDate')} to {args.get('endDate')}
        - Activities Time: from 9 AM to 6 PM
        - Travel Type: {args.get('travelType')}
        - Number of travelers: {args.get('adults')} adults, {args.get('children')} children, {args.get('infants')} infants
        - Budget Level: {args.get('budgetLevel')}
        - Entertainment Preferences: {', '.join(args.get('entertainmentPreferences', []))}

        IMPORTANT: Use this EXACT format for each activity:
        [DAY_START]
        Date: YYYY-MM-DD
        [ACTIVITY_START]
        Time: HH:MM AM/PM - HH:MM AM/PM
        Type: travel|food|activity|sightseeing|accommodation
        Description: Detailed activity description
        [ACTIVITY_END]
        [DAY_END]

        Example:
        [DAY_START]
        Date: 2025-02-22
        [ACTIVITY_START]
        Time: 9:00 AM - 10:30 AM
        Type: activity
        Description: Visit the local museum
        [ACTIVITY_END]
        [DAY_END]

        RULES:
        1. Start activities no earlier than 9:00 AM
        2. End activities no later than 7:00 PM
        3. Include lunch breaks between 12:00 PM and 2:00 PM. Suggest 2-3 specific places based on the requirements and take into account location of activities before and after lunch break.
        4. Each activity should be 1-3 hours long. If activity assumes a tour/entartainment, be more specific and share 2-3 most popular companies to choose from and why we can choose them.
        5. Use the EXACT format shown above
        6. Include 3-6 activities per day
        7. If you need to drive more than 3 hours between activities, suggest an 15-30 minute break/activity/sightseeing.
        """

    def _parse_itinerary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response into a structured itinerary format"""
        days = []
        current_day = None
        current_activities = []
        current_activity = {}
        
        # Split the response into lines and remove empty ones
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        try:
            for line in lines:
                if line == '[DAY_START]':
                    # Reset for new day
                    current_activity = {}
                    if current_day and current_activities:
                        days.append({
                            "date": current_day,
                            "activities": current_activities.copy()
                        })
                        current_activities = []
                elif line.startswith('Date: '):
                    current_day = line.replace('Date: ', '').strip()
                elif line == '[ACTIVITY_START]':
                    current_activity = {}
                elif line.startswith('Time: '):
                    current_activity['time'] = line.replace('Time: ', '').strip()
                elif line.startswith('Type: '):
                    current_activity['type'] = line.replace('Type: ', '').strip().lower()
                elif line.startswith('Description: '):
                    current_activity['description'] = line.replace('Description: ', '').strip()
                elif line == '[ACTIVITY_END]':
                    if current_activity and 'time' in current_activity and 'description' in current_activity:
                        current_activity['id'] = f"{current_day}-{len(current_activities)}"
                        current_activities.append(current_activity.copy())
                    current_activity = {}
            
            # Add the last day if exists
            if current_day and current_activities:
                days.append({
                    "date": current_day,
                    "activities": current_activities
                })

            # If no days were parsed, create a default structure
            if not days:
                logger.error(f"Failed to parse any days from response: {response_text}")
                raise ValueError("No valid days found in response")

            logger.debug(f"Parsed {len(days)} days with activities: {json.dumps(days, indent=2)}")
            return {
                "success": True,
                "generated_at": datetime.now().isoformat(),
                "days": days
            }
        except Exception as e:
            logger.error(f"Error parsing itinerary response: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Failed to parse itinerary: {str(e)}") 