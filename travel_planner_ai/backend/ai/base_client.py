from functools import wraps
from typing import Dict, Any, Optional
from cachetools import TTLCache
import hashlib
import json
import logging
from openai import OpenAI
from datetime import datetime
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

logger = logging.getLogger(__name__)

def ai_model_decorator(model: str = None):
    """Decorator to specify which model to use for the API call"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            original_model = self.model
            if model:
                self.model = model
            # Remove model from kwargs if present
            kwargs.pop('model', None)
            result = func(self, *args, **kwargs)
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
        self.client = OpenAI(api_key=api_key)
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
    def generate_itinerary(self, prompt_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a travel itinerary based on the provided arguments
        
        Args:
            prompt_args: Dictionary containing trip details
            
        Returns:
            Dictionary containing the generated itinerary
        """
        cache_key = self._generate_cache_key(prompt_args)
        
        if cache_key in self.cache:
            self._log_api_call(prompt_args, is_cached=True)
            return self.cache[cache_key]
            
        prompt = self._build_itinerary_prompt(prompt_args)
        
        try:
            model_config = get_model_config(self.model)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel planning assistant. Create detailed itineraries with specific times and activities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **model_config
            )
            
            itinerary = self._parse_itinerary_response(response.choices[0].message.content)
            self.cache[cache_key] = itinerary
            self._log_api_call(prompt_args, is_cached=False)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error with model {self.model}: {str(e)}")
            raise

    def _build_itinerary_prompt(self, args: Dict[str, Any]) -> str:
        """Build the prompt for itinerary generation"""
        return f"""
        Please create a detailed travel itinerary for a trip with the following details:
        - From: {args.get('origin')}
        - To: {args.get('destination')}
        - Dates: {args.get('startDate')} to {args.get('endDate')}
        - Travel Type: {args.get('travelType')}
        - Number of travelers: {args.get('adults')} adults, {args.get('children')} children, {args.get('infants')} infants
        - Budget Level: {args.get('budgetLevel')}
        - Entertainment Preferences: {', '.join(args.get('entertainmentPreferences', []))}
        - Intermediate Stops: {', '.join(f"{stop['destination']} ({stop['days']} days)" for stop in args.get('intermediateStops', []))}
        
        Please provide a day-by-day itinerary with specific times, activities, and relevant details.
        """

    def _parse_itinerary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and structure the AI response into a proper itinerary format"""
        # TODO: Implement proper parsing logic
        # For now, return a simple structured format
        return {
            "success": True,
            "generated_at": datetime.now().isoformat(),
            "content": response_text
        } 