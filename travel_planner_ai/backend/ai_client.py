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
from typing import Dict, Any, Optional, Literal
import hashlib
from openai import AsyncOpenAI
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

load_dotenv()  # Load environment variables from a .env file

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
    def __init__(self, api_key: str = None, cache_ttl: int = 3600, provider: str = "openai"):
        """
        Initialize the AI client with caching
        
        Args:
            api_key: OpenAI or DeepSeek API key (defaults to environment variable)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            provider: AI provider to use ("openai" or "deepseek")
        """
        self.provider = provider.lower()
        
        # Set the appropriate API key based on provider
        if self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key must be provided either directly or via OPENAI_API_KEY environment variable")
            self.base_url = None  # Use default OpenAI base URL
        elif self.provider == "deepseek":
            self.api_key = api_key or os.getenv("DS_OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("DeepSeek API key must be provided either directly or via DS_OPENAI_API_KEY environment variable")
            self.base_url = "https://api.deepseek.com/v1"
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers are 'openai' and 'deepseek'")
            
        # Initialize the client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Set the appropriate model based on provider
        self.model = self._get_default_model()
        self.cache = TTLCache(maxsize=500, ttl=cache_ttl)
        
        logger.info(f"AIClient initialized with provider: {self.provider}, model: {self.model}")
    
    def _get_default_model(self) -> str:
        """Get the default model for the selected provider"""
        if self.provider == "openai":
            return AI_CONFIG["default_model"]
        elif self.provider == "deepseek":
            return AI_CONFIG.get("deepseek_default_model", "deepseek-chat")
        return AI_CONFIG["default_model"]
    
    def _generate_cache_key(self, prompt_args: Dict[str, Any]) -> str:
        """Generate a unique cache key from the prompt arguments"""
        # Filter prompt_args to only include keys relevant for caching itinerary generation
        relevant_keys = [
            "destination", "startDate", "endDate", "travelType", "adults",
            "children", "infants", "budgetLevel", "entertainmentPreferences",
            "intermediateStops", "cuisinePreference", "language", "aiProvider"  # Added aiProvider to cache key
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
        
        # Include provider in cache key to differentiate between providers
        key_data["provider"] = self.provider
        
        # Convert to a stable string representation
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def set_provider(self, provider: Literal["openai", "deepseek"]):
        """Change the AI provider"""
        if provider not in ["openai", "deepseek"]:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers are 'openai' and 'deepseek'")
        
        # Only reinitialize if the provider is changing
        if provider != self.provider:
            logger.info(f"Changing provider from {self.provider} to {provider}")
            self.provider = provider
            
            # Set the appropriate API key based on provider
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
                self.base_url = None  # Use default OpenAI base URL
            else:  # deepseek
                self.api_key = os.getenv("DS_OPENAI_API_KEY")
                self.base_url = "https://api.deepseek.com/v1"
            
            # Reinitialize the client
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # Set the appropriate model based on provider
            self.model = self._get_default_model()
            
            # Clear cache for non-English languages to ensure language instructions are applied
            language_code = trip_request.get('language', 'en')
            if language_code != 'en':
                self.clear_cache_for_language(language_code)
    
    def _log_api_call(self, prompt_args: Dict[str, Any], is_cached: bool):
        """Log API call details"""
        logger.info(
            f"[AI-CALL] {datetime.now().isoformat()} - "
            f"Provider: {self.provider}, "
            f"Model: {self.model}, "
            f"Cached: {is_cached}, "
            f"Args: {json.dumps({k: prompt_args.get(k) for k in ['destination', 'startDate', 'endDate', 'language']}, sort_keys=True)[:100]}..."
        )

    def clear_cache_for_language(self, language_code: str):
        """Clear cache for all trips in a specific language to force regeneration with language instructions"""
        keys_to_remove = []
        for key in self.cache.keys():
            # Since cache keys are hashes, we need a different approach
            # We'll clear all cache if the language is not English to be safe
            pass
        
        # For non-English languages, clear entire cache to force regeneration
        if language_code != 'en':
            cache_size = len(self.cache)
            self.cache.clear()
            logger.info(f"[CACHE] Cleared entire cache ({cache_size} entries) for language '{language_code}' to force regeneration with language instructions")
        else:
            logger.info(f"[CACHE] No cache clearing needed for English language")

    def clear_cache_for_destination(self, destination_pattern: str):
        """Clear cache for trips matching a destination pattern"""
        keys_to_remove = []
        for key in self.cache.keys():
            if destination_pattern.lower() in key.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            logger.info(f"[CACHE] Cleared cache entry for destination pattern: {destination_pattern}")
        
        if keys_to_remove:
            logger.info(f"[CACHE] Cleared {len(keys_to_remove)} cache entries for destination pattern: {destination_pattern}")
        else:
            logger.info(f"[CACHE] No cache entries found for destination pattern: {destination_pattern}")

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
            # Set provider if specified in the request
            if "aiProvider" in trip_request:
                self.set_provider(trip_request["aiProvider"])
                logger.info(f"Using AI provider from request: {self.provider}")
            
            # Handle deprecated model names
            if self.model == "gpt-4-turbo-8k": # This specific string check
                logger.warning(f"Model '{self.model}' is deprecated, using '{AI_CONFIG['default_model']}' instead")
                self.model = self._get_default_model()
            
            # Clear cache for non-English languages to ensure language instructions are applied
            language_code = trip_request.get('language', 'en')
            if language_code != 'en':
                self.clear_cache_for_language(language_code)
                
            cache_key = self._generate_cache_key(trip_request)
            
            if cache_key in self.cache:
                self._log_api_call(trip_request, is_cached=True)
                cached_result = self.cache[cache_key]
                
                # Validate cached result for completeness
                expected_days = self._calculate_expected_days(trip_request)
                if len(cached_result.get('days', [])) >= expected_days:
                    return cached_result
                else:
                    logger.warning(f"[CACHE] Cached result incomplete ({len(cached_result.get('days', []))} vs {expected_days} days), regenerating")
                    del self.cache[cache_key]  # Remove incomplete cached result
            
            self._log_api_call(trip_request, is_cached=False)
            
            # Try up to 3 attempts for complete response
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Generate different prompts for retry attempts
                    if attempt == 0:
                        prompt = self._generate_prompt(trip_request)
                        system_content = f"""You are a travel planning assistant. Your PRIMARY job is to complete ALL requested days.

🚨 CRITICAL: You MUST generate itineraries for ALL requested days. NEVER stop early.

COMPLETION RULES:
1. Count the requested days and provide exactly that many [DAY_START] blocks
2. If running low on space, use shorter descriptions but COMPLETE ALL DAYS
3. Each day needs minimum 3-4 activities, maximum detail within space limits
4. NEVER truncate - better to have brief but complete days than detailed incomplete ones

QUALITY STANDARDS:
- Match user preferences and budget
- Include specific place names and recommendations
- Family-friendly considerations
- Practical timing and logistics

SUCCESS = ALL days completed. FAILURE = Missing any day."""
                    else:
                        # More aggressive prompts for retries
                        expected_days = self._calculate_expected_days(trip_request)
                        prompt = self._generate_aggressive_retry_prompt(trip_request, attempt, expected_days)
                        system_content = f"""⚠️ RETRY #{attempt + 1}: PREVIOUS INCOMPLETE!

🚨 YOU MUST COMPLETE ALL {expected_days} DAYS THIS TIME.

MANDATORY:
- Generate {expected_days} [DAY_START] blocks
- Use shorter descriptions if needed
- NEVER stop before completing all days
- Focus on coverage over excessive detail

THIS IS CRITICAL."""

                    logger.info(f"Sending request to {self.provider.upper()} with model {self.model} (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Prompt structure: { {key: type(val) for key, val in json.loads(prompt).items()} if isinstance(prompt,str) and prompt.startswith('{') else 'String prompt' }")
                    logger.info(f"System message length: {len(system_content)} chars")
                    logger.info(f"User prompt length: {len(prompt)} chars")

                    # The prompt from _generate_prompt is a single string, not system/user pair
                    # The old call_openai_api took a single prompt string and constructed messages.
                    # The AIClient's direct call to completions.create needs messages.
                    # Let's adjust to ensure messages are built correctly here or in _generate_prompt
                    
                    user_content = prompt # Assuming _generate_prompt returns the user part of the prompt

                    # Get base model config and modify for retry attempts
                    model_config = get_model_config(self.model).copy()
                    if attempt > 0:
                        # For retries, increase temperature slightly and reduce max_tokens significantly to force completion
                        model_config['temperature'] = min(0.5, model_config.get('temperature', 0.3) + 0.1)
                        model_config['max_tokens'] = 10000  # Significantly reduced to force shorter, complete responses
                        logger.info(f"Retry attempt {attempt + 1}: Using temperature={model_config['temperature']}, max_tokens={model_config['max_tokens']}")
                    else:
                        logger.info(f"First attempt: Using temperature={model_config.get('temperature', 0.3)}, max_tokens={model_config.get('max_tokens', 14000)}")

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
                        **model_config # Use modified model config
                    )
                    
                    if not response or not response.choices or not response.choices[0].message:
                        raise ValueError("Invalid response structure from API")
                        
                    logger.info(f"Received response from {self.provider.upper()}")
                    # logger.debug(f"Raw response: {response}") # Can be very verbose
                    
                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError(f"Empty content in response from {self.provider.upper()} API")
                    
                    logger.info(f"Response content length: {len(content)} characters")
                    logger.info(f"Response contains {content.count('[DAY_START]')} [DAY_START] blocks")
                    logger.info(f"Response contains {content.count('[DAY_END]')} [DAY_END] blocks")
                    
                    # Enhanced token usage logging and storage
                    token_usage = None
                    if hasattr(response, 'usage') and response.usage:
                        token_usage = {
                            'total_tokens': response.usage.total_tokens,
                            'prompt_tokens': response.usage.prompt_tokens,
                            'completion_tokens': response.usage.completion_tokens
                        }
                        logger.info(f"🪙 TOKEN USAGE: {token_usage['total_tokens']} total ({token_usage['prompt_tokens']} prompt + {token_usage['completion_tokens']} completion)")
                    else:
                        logger.warning("No token usage information available from API response")
                        
                    itinerary = await self._process_response(content, trip_request)
                    
                    # Add token usage to the response if available
                    if token_usage:
                        itinerary['token_usage'] = token_usage
                    
                    # Check if response is complete
                    expected_days = self._calculate_expected_days(trip_request)
                    actual_days = len(itinerary.get('days', []))
                    
                    if actual_days >= expected_days:
                        logger.info(f"[SUCCESS] Complete itinerary generated with {actual_days} days on attempt {attempt + 1}")
                        if token_usage:
                            logger.info(f"[SUCCESS] Final token cost: {token_usage['total_tokens']} tokens")
                        self.cache[cache_key] = itinerary
                        return itinerary
                    else:
                        logger.warning(f"[RETRY] Incomplete response: got {actual_days}/{expected_days} days on attempt {attempt + 1}")
                        if token_usage:
                            logger.warning(f"[RETRY] Wasted {token_usage['total_tokens']} tokens on incomplete response")
                        if attempt < max_retries - 1:
                            logger.info(f"[RETRY] Retrying with attempt {attempt + 2}/{max_retries}")
                            continue
                        else:
                            logger.error(f"[FINAL ATTEMPT] All {max_retries} attempts returned incomplete responses, using partial result")
                            if token_usage:
                                logger.error(f"[FINAL ATTEMPT] Total tokens used across all attempts: Check logs for sum")
                            self.cache[cache_key] = itinerary
                            return itinerary
                    
                except openai.APIError as api_error:
                    logger.error(f"{self.provider.upper()} API error during completions.create (attempt {attempt + 1}): {str(api_error)}")
                    if attempt < max_retries - 1:
                        logger.info(f"[RETRY] API error, retrying attempt {attempt + 2}/{max_retries}")
                        continue
                    else:
                        raise ValueError(f"{self.provider.upper()} API error: {str(api_error)}") 
                except Exception as e_api_call:
                    logger.error(f"Unexpected error during {self.provider.upper()} API call (attempt {attempt + 1}): {str(e_api_call)}", exc_info=True)
                    if attempt < max_retries - 1:
                        logger.info(f"[RETRY] Unexpected error, retrying attempt {attempt + 2}/{max_retries}")
                        continue
                    else:
                        raise ValueError(f"Unexpected error during API call: {str(e_api_call)}")
            
        except ValueError as ve:
            logger.error(f"ValueError in generate_itinerary: {str(ve)}", exc_info=True)
            return self._create_fallback_itinerary(trip_request)
        except Exception as e:
            logger.error(f"Error generating itinerary with {self.provider} model {self.model}: {str(e)}", exc_info=True) 
            return self._create_fallback_itinerary(trip_request)

    def _calculate_expected_days(self, trip_request: Dict[str, Any]) -> int:
        """Calculate the expected number of days for a trip"""
        from datetime import datetime
        start_date = datetime.strptime(trip_request.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(trip_request.get('endDate'), '%Y-%m-%d')
        return (end_date - start_date).days + 1

    def _generate_prompt(self, args: Dict[str, Any]) -> str:
        """Generate a prompt for the AI model.
        This prompt is expected to be the 'user' part of the chat messages.
        """
        # Calculate expected number of days for validation
        from datetime import datetime, timedelta
        start_date = datetime.strptime(args.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(args.get('endDate'), '%Y-%m-%d')
        expected_days = (end_date - start_date).days + 1
        
        # Format intermediate stops if they exist
        intermediate_stops_text = ""
        if args.get('intermediateStops') and len(args.get('intermediateStops')) > 0:
            stops = []
            for stop_data in args.get('intermediateStops'):
                if isinstance(stop_data, dict):
                    dest = stop_data.get('destination', 'Unknown')
                    days = stop_data.get('days', 1)
                    stops.append(f"{dest} ({days} days)")
                else:
                    stops.append(str(stop_data))
            intermediate_stops_text = f" via {', '.join(stops)}"

        # Route-based geographic logic (works for any country)
        destination = args.get('destination', 'Destination')
        origin = args.get('origin', 'Origin')
        if origin != 'Origin' and destination != 'Destination':
            geographic_context = f"🗺️ ROUTE LOGIC: ALL activities must be along or near the route from {origin} to {destination}. Suggest activities that make geographic sense for travelers moving between these locations."
        else:
            geographic_context = f"🗺️ STAY NEAR {destination.upper()}: All activities must be within reasonable distance of {destination}."

        # Generate date list for completion tracking
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        dates_text = ', '.join(date_list)

        # Language instruction mapping
        language_code = args.get('language', 'en')
        language_instructions = {
            'en': 'RESPOND IN ENGLISH',
            'es': 'RESPONDE EN ESPAÑOL (Spanish)',
            'fr': 'RÉPONDEZ EN FRANÇAIS (French)', 
            'de': 'ANTWORTEN SIE AUF DEUTSCH (German)',
            'it': 'RISPONDI IN ITALIANO (Italian)',
            'ru': 'ОТВЕЧАЙТЕ НА РУССКОМ ЯЗЫКЕ (Russian) - Все описания деятельности, местоположения и объяснения должны быть на русском языке',
            'zh': '用中文回答 (Chinese) - All activity descriptions and explanations should be in Chinese'
        }
        
        language_instruction = language_instructions.get(language_code, 'RESPOND IN ENGLISH')

        prompt = f"""🎯 CRITICAL: Generate complete itinerary for ALL {expected_days} days: {dates_text}

🌍 LANGUAGE REQUIREMENT: {language_instruction}

📍 Trip: {args.get('travelType', 'trip')} from {origin} to {destination}{intermediate_stops_text}
👥 Travelers: {args.get('adults', 2)} adults, {args.get('children', 0)} children  
💰 Budget: {args.get('budgetLevel', 'mid-range')}
🎭 Preferences: {', '.join(args.get('entertainmentPreferences', []))}

{geographic_context}

⚠️ COMPLETION REQUIREMENTS:
- MUST include ALL {expected_days} days from {dates_text}
- NEVER stop early or skip days
- Each day needs 3-5 activities

🚨 FILTER ACCURACY REQUIREMENTS (MANDATORY):
- ALL activities MUST match user preferences: {', '.join(args.get('entertainmentPreferences', []))}
- ALL activities MUST fit {args.get('budgetLevel', 'mid-range')} budget level
- ALL activities MUST be suitable for {args.get('adults', 2)} adults + {args.get('children', 0)} children
- NO activities that contradict user filters

📋 QUALITY RULES:
1. **Elaborative Descriptions**: Write comprehensive 3-4 sentence descriptions that thoroughly explain the activity. Include specific details, insider tips, what makes this unique, historical context, practical information, and what visitors will experience. Be detailed and informative.
2. **Elaborative "Why" Explanations**: Provide detailed explanations of exactly how each activity aligns with user preferences ({', '.join(args.get('entertainmentPreferences', []))}) and budget ({args.get('budgetLevel', 'mid-range')}). Explain comprehensively why this fits their travel style, family needs, and specific interests.
3. **Precise Location Names**: Include exact venue names, addresses, and landmarks (coordinates no required)
4. **Cultural Context**: Add historical significance, local insights, or unique features that elevate the experience
5. **Practical Info**: Include timing, difficulty, age-appropriateness, duration, and insider knowledge
6. **Specific Names**: Use actual restaurant names, tour operators, exact addresses when possible
7. **Budget Compliance**: Match {args.get('budgetLevel', 'mid-range')} pricing expectations with specific cost insights
8. **Route Logic**: Activities should make geographic sense along the travel route

🏗️ FORMAT (use exact structure):
[DAY_START]
Date: YYYY-MM-DD

[ACTIVITY_START]
Time: HH:MM - HH:MM
Type: travel/food/sightseeing/activity/accommodation
Price: free/$/$$/$$$ 
Location: Specific venue name, City, State/Province
Description: Write an elaborative, comprehensive description that thoroughly covers what this activity entails. Include specific details about what visitors will see, do, and experience. Mention unique features, historical context, local significance, and practical insights. Provide insider tips, best times to visit, what to expect, and detailed information that helps travelers understand the full value and appeal of this activity.
Why: Provide an elaborative explanation that comprehensively details how this activity specifically matches the user's {', '.join(args.get('entertainmentPreferences', []))} preferences, suits their {args.get('budgetLevel', 'mid-range')} budget, accommodates {args.get('adults', 2)} adults and {args.get('children', 0)} children, and enhances their {args.get('travelType', 'trip')} experience. Be thorough in explaining the connections to their filters and requirements.
[ACTIVITY_END]

[DAY_END]

🎯 SUCCESS = ALL {expected_days} days completed with filter-accurate, elaborative content"""

        # TODO: Deprecated Coordinates June 2025 - coordinates no longer included in prompt
        # Old code: 2. **Precise Coordinates Required**: Include accurate coordinates for every location: "coordinates": {{"latitude": X.XXXX, "longitude": -X.XXXX}}. Use exact coordinates for landmarks, attractions, and specific businesses - NOT approximate city coordinates.

        return prompt

    def _generate_aggressive_retry_prompt(self, args: Dict[str, Any], attempt: int, expected_days: int) -> str:
        """Generate a focused retry prompt that prioritizes completion with essential quality"""
        from datetime import datetime, timedelta
        start_date = datetime.strptime(args.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(args.get('endDate'), '%Y-%m-%d')
        
        # Generate list of all expected dates
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Extract destination for geographic enforcement
        destination = args.get('destination', 'Destination')
        origin = args.get('origin', 'Origin')
        if origin != 'Origin' and destination != 'Destination':
            geographic_context = f"🗺️ STAY ON ROUTE: {origin} → {destination}!"
        else:
            geographic_context = f"🗺️ STAY NEAR {destination.upper()}!"

        urgency_level = ["🔥 URGENT", "🚨 CRITICAL", "⚠️ FINAL ATTEMPT"][min(attempt-1, 2)]
        
        # Language instruction mapping
        language_code = args.get('language', 'en')
        language_instructions = {
            'en': 'RESPOND IN ENGLISH',
            'es': 'RESPONDE EN ESPAÑOL',
            'fr': 'RÉPONDEZ EN FRANÇAIS', 
            'de': 'ANTWORTEN SIE AUF DEUTSCH',
            'it': 'RISPONDI IN ITALIANO',
            'ru': 'ОТВЕЧАЙТЕ НА РУССКОМ ЯЗЫКЕ',
            'zh': '用中文回答'
        }
        
        language_instruction = language_instructions.get(language_code, 'RESPOND IN ENGLISH')
        
        # Retry with emphasis on both completion AND coordinates
        retry_prompt = f"""{urgency_level}: Generate ALL {expected_days} days: {', '.join(date_list)}

🌍 LANGUAGE: {language_instruction}

{geographic_context}
👥 {args.get('adults', 2)} adults + {args.get('children', 0)} children | 💰 {args.get('budgetLevel', 'mid-range')}
🎭 Preferences: {', '.join(args.get('entertainmentPreferences', []))}

📋 MANDATORY:
- ALL {expected_days} days required: {', '.join(date_list)}
- MUST match user filters: {', '.join(args.get('entertainmentPreferences', []))}
- MUST fit {args.get('budgetLevel', 'mid-range')} budget
- Include specific venue names and exact addresses
- Elaborative descriptions and why explanations
- COMPLETE coverage first, quality second

FORMAT:
[DAY_START]
Date: YYYY-MM-DD
[ACTIVITY_START]  
Time: HH:MM - HH:MM
Type: travel/food/activity/sightseeing
Price: free/$/$$/$$$ 
Location: Venue name, City, State
Description: Elaborative description with comprehensive details, insider tips, historical context, and specific information about what visitors will experience. Be thorough and informative.
Why: Elaborative explanation of how this activity specifically matches {', '.join(args.get('entertainmentPreferences', []))} preferences, fits {args.get('budgetLevel', 'mid-range')} budget, and suits family composition ({args.get('adults', 2)} adults + {args.get('children', 0)} children). Be comprehensive.
[ACTIVITY_END]
[DAY_END]

✅ SUCCESS = {expected_days} complete days with filter-accurate, elaborative content"""

        # TODO: Deprecated Coordinates June 2025 - coordinates no longer requested in retry prompt
        # Old code: - Include precise coordinates for every location (not approximate city coordinates)
        # Old code: Coordinates: latitude, longitude

        return retry_prompt

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
            # TODO: Deprecated Coordinates June 2025 - coordinate parsing function no longer used
            return None
            # if coords_str.lower() in ['n/a', 'not available', '']:
            #     return None
            # for pattern in COORDINATE_PATTERNS:
            #     match = pattern.search(coords_str)
            #     if match:
            #         try:
            #             lat = float(match.group(1))
            #             lon = float(match.group(2))
            #             if -90 <= lat <= 90 and -180 <= lon <= 180:
            #                 # Additional validation: check if coordinates are reasonable for the destination
            #                 destination = args.get('destination', '').lower()
            #                 if not self._validate_coordinate_region(lat, lon, destination):
            #                     logger.warning(f"Coordinates {lat}, {lon} seem inconsistent with destination '{destination}' - but allowing anyway")
            #                 return {'latitude': lat, 'longitude': lon}
            #         except (ValueError, IndexError, TypeError):
            #             continue # Try next pattern
            # logger.warning(f"Invalid or unparseable coordinates format: '{coords_str}'")
            # return None

        try:
            # Calculate expected number of days for validation
            from datetime import datetime, timedelta
            start_date = datetime.strptime(args.get('startDate'), '%Y-%m-%d')
            end_date = datetime.strptime(args.get('endDate'), '%Y-%m-%d')
            expected_days = (end_date - start_date).days + 1
            
            if not self._validate_response(response, args):
                logger.error("AI response failed validation.")
                raise ValueError("Invalid response format after validation")

            days = []
            raw_days = response.split('[DAY_START]')[1:]
            
            logger.info(f"[DEBUG] Expected {expected_days} days, found {len(raw_days)} day blocks in AI response")

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
                    # TODO: Deprecated Activity ID June 2025 - activity ID generation no longer needed
                    # activity_data = {'id': f"{day_dict['date']}-{uuid.uuid4()}"}
                    activity_data = {}
                    
                    time_match = RE_TIME.search(activity_text)
                    activity_data['time'] = time_match.group(1).strip() if time_match else "Time not specified"
                    
                    type_match = RE_TYPE.search(activity_text)
                    activity_type_str = type_match.group(1).lower() if type_match else 'activity'
                    activity_data['type'] = 'food' if activity_type_str == 'lunch' else activity_type_str
                    
                    price_match = RE_PRICE.search(activity_text)
                    activity_data['price'] = price_match.group(1) if price_match else '$$'
                    
                    location_match = RE_LOCATION.search(activity_text)
                    activity_data['location'] = location_match.group(1).strip() if location_match else "Location not specified"
                    
                    # TODO: Deprecated Coordinates June 2025 - coordinate parsing no longer performed
                    # coords_match_text = RE_COORDINATES_TEXT.search(activity_text)
                    # if coords_match_text:
                    #     parsed_coords = parse_coordinates(coords_match_text.group(1).strip())
                    #     if parsed_coords:
                    #         activity_data['coordinates'] = parsed_coords
                    
                    desc_match = RE_DESCRIPTION.search(activity_text)
                    activity_data['description'] = desc_match.group(1).strip() if desc_match else "No description provided."
                    
                    why_match = RE_WHY.search(activity_text)
                    activity_data['why'] = why_match.group(1).strip() if why_match else "Recommended based on travel preferences."
                    
                    activities.append(activity_data)
                
                if activities:
                    day_dict['activities'] = activities
                    days.append(day_dict)

            # Check if we got all expected days
            if len(days) < expected_days:
                logger.error(f"[INCOMPLETE RESPONSE] Expected {expected_days} days but only got {len(days)} days in AI response")
                logger.error(f"[INCOMPLETE RESPONSE] Missing days detected. This could be due to token limits or AI truncation.")
                
                # Log the actual dates we got vs expected
                received_dates = [day['date'] for day in days]
                expected_dates = []
                current_date = start_date
                while current_date <= end_date:
                    expected_dates.append(current_date.strftime('%Y-%m-%d'))
                    current_date += timedelta(days=1)
                
                missing_dates = set(expected_dates) - set(received_dates)
                logger.error(f"[INCOMPLETE RESPONSE] Expected dates: {expected_dates}")
                logger.error(f"[INCOMPLETE RESPONSE] Received dates: {received_dates}")
                logger.error(f"[INCOMPLETE RESPONSE] Missing dates: {list(missing_dates)}")
                
                # For now, return what we have and let the fallback handle the missing days
                # In future iterations, we could implement retry logic here
                if len(days) == 0:
                    raise ValueError(f"No valid days found in AI response")
                else:
                    logger.warning(f"[INCOMPLETE RESPONSE] Returning partial itinerary with {len(days)} out of {expected_days} days")

            logger.info(f"[DEBUG] Successfully processed {len(days)} days out of {expected_days} expected")
            
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
                        # TODO: Deprecated Activity ID June 2025 - activity ID generation no longer needed for fallback
                        # "id": str(uuid.uuid4()), 
                        "time": "10:00 AM - 12:00 PM", "type": "activity",
                        "description": f"Explore {destination}", "location": destination,
                        "price": "$$", "why": "Default exploration activity."
                    },
                    {
                        # TODO: Deprecated Activity ID June 2025 - activity ID generation no longer needed for fallback
                        # "id": str(uuid.uuid4()), 
                        "time": "12:30 PM - 2:00 PM", "type": "food",
                        "description": "Lunch at a local spot", "location": "Local Restaurant",
                        "price": "$$", "why": "Enjoy a meal."
                    },
                    {
                        # TODO: Deprecated Activity ID June 2025 - activity ID generation no longer needed for fallback
                        # "id": str(uuid.uuid4()), 
                        "time": "2:30 PM - 5:30 PM", "type": "sightseeing",
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

    def _validate_coordinate_region(self, latitude: float, longitude: float, destination: str) -> bool:
        """
        TODO: Deprecated Coordinates June 2025 - coordinate validation function no longer used
        Validate if the given coordinates are reasonable for the destination region
        """
        return True  # Always return True since coordinates are deprecated
        # try:
        #     # Basic regional validation for major destinations
        #     region_bounds = {
        #         # United States (contiguous)
        #         'usa': {'lat_min': 24.0, 'lat_max': 49.0, 'lon_min': -125.0, 'lon_max': -66.0},
        #         'california': {'lat_min': 32.5, 'lat_max': 42.0, 'lon_min': -124.5, 'lon_max': -114.0},
        #         'oregon': {'lat_min': 42.0, 'lat_max': 46.3, 'lon_min': -124.6, 'lon_max': -116.5},
        #         'redding': {'lat_min': 40.4, 'lat_max': 40.7, 'lon_min': -122.5, 'lon_max': -122.2},
        #         'portland': {'lat_min': 45.4, 'lat_max': 45.7, 'lon_min': -122.8, 'lon_max': -122.5},
        #         'campbell': {'lat_min': 37.2, 'lat_max': 37.3, 'lon_min': -122.1, 'lon_max': -121.9},
        #         
        #         # Canada
        #         'canada': {'lat_min': 41.7, 'lat_max': 83.1, 'lon_min': -141.0, 'lon_max': -52.6},
        #         'british columbia': {'lat_min': 48.3, 'lat_max': 60.0, 'lon_min': -139.1, 'lon_max': -114.0},
        #         'vancouver': {'lat_min': 49.2, 'lat_max': 49.3, 'lon_min': -123.3, 'lon_max': -123.0},
        #         
        #         # Europe
        #         'france': {'lat_min': 41.3, 'lat_max': 51.1, 'lon_min': -5.1, 'lon_max': 9.6},
        #         'italy': {'lat_min': 35.5, 'lat_max': 47.1, 'lon_min': 6.6, 'lon_max': 18.8},
        #         'spain': {'lat_min': 35.2, 'lat_max': 43.8, 'lon_min': -9.3, 'lon_max': 4.3},
        #         'germany': {'lat_min': 47.3, 'lat_max': 55.1, 'lon_min': 5.9, 'lon_max': 15.0},
        #     }
        #     
        #     # Check against specific city/region bounds first
        #     for region, bounds in region_bounds.items():
        #         if region in destination:
        #             if (bounds['lat_min'] <= latitude <= bounds['lat_max'] and 
        #                 bounds['lon_min'] <= longitude <= bounds['lon_max']):
        #                 return True
        #             else:
        #                 logger.warning(f"Coordinates {latitude}, {longitude} outside expected bounds for {region}")
        #                 return False
        #     
        #     # If no specific region found, check broader regions
        #     if any(term in destination for term in ['california', 'ca', 'oregon', 'or', 'usa', 'united states']):
        #         bounds = region_bounds['usa']
        #         return (bounds['lat_min'] <= latitude <= bounds['lat_max'] and 
        #                bounds['lon_min'] <= longitude <= bounds['lon_max'])
        #     
        #     if any(term in destination for term in ['canada', 'british columbia', 'bc']):
        #         bounds = region_bounds['canada']
        #         return (bounds['lat_min'] <= latitude <= bounds['lat_max'] and 
        #                bounds['lon_min'] <= longitude <= bounds['lon_max'])
        #     
        #     # Default to valid if we can't determine the region
        #     return True
        #     
        # except Exception as e:
        #     logger.warning(f"Error validating coordinates: {e}")
        #     return True  # Default to valid if validation fails

# Define what should be exported from this module if it were a library
# For application use, this is less critical but good practice.
__all__ = [
    'AIClient',
]
