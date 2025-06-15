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
from langdetect import detect
from typing import Dict, Any, Optional, Literal
import hashlib
from openai import AsyncOpenAI
from travel_planner_ai.backend.config.ai_config import AI_CONFIG, get_model_config

load_dotenv(dotenv_path="travel_planner_ai/.env")  # Load environment variables from the correct .env file

# Set up logging
logger = logging.getLogger(__name__)

# Environment-based debug control
DEBUG_LOGGING_ENABLED = os.getenv('AI_DEBUG_LOGGING', 'false').lower() in ('true', '1', 'yes', 'on')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

# Enable debug logging in development/testing environments
if ENVIRONMENT in ('development', 'testing', 'dev', 'test') or DEBUG_LOGGING_ENABLED:
    DEBUG_LOGGING_ENABLED = True
    logger.info("🔍 Debug logging enabled for AI client")
else:
    DEBUG_LOGGING_ENABLED = False
    logger.info("🔇 Debug logging disabled for production environment")

def _debug_log_prompts(attempt: int, system_content: str, prompt: str):
    """Log prompt details only in debug mode"""
    if not DEBUG_LOGGING_ENABLED:
        return
    
    logger.info(f"[PROMPT DEBUG] === SYSTEM MESSAGE (attempt {attempt + 1}) ===")
    logger.info(f"[PROMPT DEBUG] {system_content}")
    logger.info(f"[PROMPT DEBUG] === USER PROMPT (attempt {attempt + 1}) ===")
    logger.info(f"[PROMPT DEBUG] {prompt[:1000]}{'...' if len(prompt) > 1000 else ''}")
    logger.info(f"[PROMPT DEBUG] === END PROMPTS ===")

def _debug_log_response(attempt: int, content: str):
    """Log full response only in debug mode"""
    if not DEBUG_LOGGING_ENABLED:
        return
    
    logger.info(f"[RESPONSE DEBUG] === FULL AI RESPONSE (attempt {attempt + 1}) ===")
    logger.info(f"[RESPONSE DEBUG] {content}")
    logger.info(f"[RESPONSE DEBUG] === END RESPONSE ===")

def _debug_log_response_structure(content: str, expected_days: int):
    """Log response structure analysis only in debug mode"""
    if not DEBUG_LOGGING_ENABLED:
        return
    
    day_starts = content.count('[DAY_START]')
    day_ends = content.count('[DAY_END]')
    activity_starts = content.count('[ACTIVITY_START]')
    activity_ends = content.count('[ACTIVITY_END]')
    
    logger.info(f"[STRUCTURE DEBUG] Day blocks: {day_starts} starts, {day_ends} ends")
    logger.info(f"[STRUCTURE DEBUG] Activity blocks: {activity_starts} starts, {activity_ends} ends")
    logger.info(f"[STRUCTURE DEBUG] Expected days: {expected_days}, Found days: {day_starts}")
    
    # Check if response was truncated
    if content.endswith('...') or not content.endswith('[DAY_END]'):
        logger.warning(f"[TRUNCATION DEBUG] Response appears to be truncated!")
        logger.warning(f"[TRUNCATION DEBUG] Last 200 chars: {content[-200:]}")

def _debug_log_token_analysis(token_usage: dict, model: str, provider: str, content: str = None):
    """Log detailed token analysis only in debug mode"""
    if not DEBUG_LOGGING_ENABLED or not token_usage:
        return
    
    from travel_planner_ai.backend.config.ai_config import get_model_config
    model_config = get_model_config(model)
    max_tokens_setting = model_config.get('max_tokens', 16000)
    
    # Calculate percentages
    prompt_pct = (token_usage['prompt_tokens'] / token_usage['total_tokens']) * 100
    completion_pct = (token_usage['completion_tokens'] / token_usage['total_tokens']) * 100
    utilization_pct = (token_usage['total_tokens'] / max_tokens_setting) * 100
    
    logger.info(f"[TOKEN ANALYSIS] === DETAILED TOKEN BREAKDOWN ===")
    logger.info(f"[TOKEN ANALYSIS] Model: {model} | Provider: {provider.upper()}")
    logger.info(f"[TOKEN ANALYSIS] Max tokens setting: {max_tokens_setting}")
    logger.info(f"[TOKEN ANALYSIS] Prompt overhead: {token_usage['prompt_tokens']} tokens ({prompt_pct:.1f}%)")
    logger.info(f"[TOKEN ANALYSIS] Content generated: {token_usage['completion_tokens']} tokens ({completion_pct:.1f}%)")
    logger.info(f"[TOKEN ANALYSIS] Total utilization: {token_usage['total_tokens']}/{max_tokens_setting} ({utilization_pct:.1f}%)")
    
    # Tokens per day analysis if content is provided
    if content:
        days_found = content.count('[DAY_START]')
        if days_found > 0:
            tokens_per_day = token_usage['completion_tokens'] / days_found
            logger.info(f"[TOKEN ANALYSIS] Tokens per day generated: {tokens_per_day:.1f}")
            if tokens_per_day < 200:
                logger.warning(f"[TOKEN ANALYSIS] LOW DETAIL: Only {tokens_per_day:.1f} tokens per day - content may be too brief")
    
    # Efficiency warnings with more context
    if prompt_pct > 40:
        logger.warning(f"[TOKEN ANALYSIS] HIGH PROMPT OVERHEAD: {prompt_pct:.1f}% - consider shorter prompts")
    if utilization_pct < 50:
        logger.warning(f"[TOKEN ANALYSIS] LOW UTILIZATION: Only {utilization_pct:.1f}% of available tokens used")
    if token_usage['completion_tokens'] < 1000:
        logger.warning(f"[TOKEN ANALYSIS] SHORT COMPLETION: Only {token_usage['completion_tokens']} completion tokens - AI may be stopping early")
    
    logger.info(f"[TOKEN ANALYSIS] === END TOKEN ANALYSIS ===")

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
        self.cache = TTLCache(maxsize=500, ttl=cache_ttl)
        self._setup_provider(provider, api_key)
        
        logger.info(f"AIClient initialized with provider: {self.provider}, model: {self.model}")
    
    def _setup_provider(self, provider: str, api_key: str = None):
        """Setup provider configuration and initialize client"""
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
                logger.warning("DeepSeek API key not found (DS_OPENAI_API_KEY). Falling back to OpenAI.")
                # Fallback to OpenAI
                self.provider = "openai"
                self.api_key = os.getenv("OPENAI_API_KEY")
                self.base_url = None
                if not self.api_key:
                    raise ValueError("Neither DeepSeek nor OpenAI API keys found. Please set DS_OPENAI_API_KEY or OPENAI_API_KEY environment variables.")
            else:
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
    
    def _get_default_model(self) -> str:
        """Get the default model for the selected provider"""
        if self.provider == "openai":
            return AI_CONFIG["default_model"]
        elif self.provider == "deepseek":
            return AI_CONFIG.get("deepseek_default_model", "deepseek-chat")
        return AI_CONFIG["default_model"]
    
    def _generate_cache_key(self, prompt_args: Dict[str, Any]) -> str:
        """Generate a unique cache key from the prompt arguments"""
        # Include ALL fields that affect trip generation to ensure correct caching
        relevant_keys = [
            "userId", "destination", "startDate", "endDate", "travelType", 
            "adults", "children", "infants", "budgetLevel", "language",
            "entertainmentPreferences", "cuisinePreference", "origin",
            "exclusionRadius", "exclusionUnit"
        ]
        
        key_data = {}
        for key in relevant_keys:
            value = prompt_args.get(key)
            if isinstance(value, list):
                # Sort lists for consistent hashing
                key_data[key] = sorted(value) if value else []
            else:
                key_data[key] = value
        
        key_data["provider"] = self.provider
        
        # Convert to a stable string representation
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _generate_activity_cache_key(self, original_activity: dict, custom_preferences: str, activity_type: str, is_meal: bool) -> str:
        """Generate cache key for activity refresh to avoid redundant API calls"""
        cache_data = {
            "original_location": original_activity.get('location', ''),
            "original_time": original_activity.get('time', ''),
            "custom_preferences": custom_preferences,
            "activity_type": activity_type,
            "is_meal": is_meal,
            "provider": self.provider
        }
        return hashlib.sha256(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def set_provider(self, provider: Literal["openai", "deepseek"]):
        """Change the AI provider"""
        if provider not in ["openai", "deepseek"]:
            raise ValueError(f"Unsupported provider: {provider}. Supported providers are 'openai' and 'deepseek'")
        
        # Only reinitialize if the provider is changing
        if provider != self.provider:
            logger.info(f"Changing provider from {self.provider} to {provider}")
            self._setup_provider(provider)
            logger.info(f"Provider successfully changed to {self.provider} with model {self.model}")
    
    def _log_api_call(self, prompt_args: Dict[str, Any], is_cached: bool):
        """Log API call details"""
        logger.info(
            f"[AI-CALL] {datetime.now().isoformat()} - "
            f"Provider: {self.provider}, "
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
            # Set provider if specified in the request
            if "aiProvider" in trip_request:
                self.set_provider(trip_request["aiProvider"])
                logger.info(f"Using AI provider from request: {self.provider}")
            
            # Handle deprecated model names
            if self.model == "gpt-4-turbo-8k": # This specific string check
                logger.warning(f"Model '{self.model}' is deprecated, using '{AI_CONFIG['default_model']}' instead")
                self.model = self._get_default_model()
            
            # CRITICAL FIX: Calculate expected_days BEFORE using it anywhere
            expected_days = self._calculate_expected_days(trip_request)
            logger.info(f"Calculated expected days: {expected_days}")
            
            cache_key = self._generate_cache_key(trip_request)
            
            if cache_key in self.cache:
                self._log_api_call(trip_request, is_cached=True)
                cached_result = self.cache[cache_key]
                
                # Smarter cache validation - check quality not just quantity
                cached_days = len(cached_result.get('days', []))
                if cached_days >= expected_days:
                    # Validate that cached days have reasonable activity count
                    total_activities = sum(len(day.get('activities', [])) for day in cached_result.get('days', []))
                    avg_activities_per_day = total_activities / cached_days if cached_days > 0 else 0
                    
                    if avg_activities_per_day >= 2:  # At least 2 activities per day on average
                        logger.info(f"[CACHE HIT] Using cached result with {cached_days} days, {total_activities} activities")
                        return cached_result
                    else:
                        logger.warning(f"[CACHE QUALITY] Cached result has too few activities ({avg_activities_per_day:.1f} per day), regenerating")
                        del self.cache[cache_key]
                elif cached_days >= (expected_days * 0.8):  # If we have 80%+ of days, keep it
                    logger.info(f"[CACHE PARTIAL] Using partially cached result ({cached_days}/{expected_days} days)")
                    return cached_result
                else:
                    logger.warning(f"[CACHE INCOMPLETE] Cached result too incomplete ({cached_days}/{expected_days} days), regenerating")
                    del self.cache[cache_key]
            
            self._log_api_call(trip_request, is_cached=False)
            
            # Try up to 3 attempts for complete response
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Generate different prompts for retry attempts
                    if attempt == 0:
                        # First attempt: Detailed system message focused on quality
                        system_content = f"""You are a travel planning expert. Generate a high-quality itinerary for {expected_days} days.

QUALITY FIRST: Focus on accuracy, detail, and user preference matching over forced completion.

QUALITY STANDARDS:
1. **Detailed Descriptions**: 2-3 sentences with specific details, insider tips, historical context
2. **Precise Preference Matching**: Explain exactly how each activity matches user preferences: {', '.join(trip_request.get('entertainmentPreferences', []))}
3. **Single Activity Types**: Use ONE type per activity from user preferences, never combine types
4. **Mandatory Food Activities**: Include at least 1 dining activity per day (type "food")
5. **Accurate Information**: Specific venue names, addresses, practical details
6. **Budget Compliance**: Match {trip_request.get('budgetLevel', 'mid-range')} pricing expectations
7. **Geographic Logic**: Ensure activities make geographic sense for the trip type

Generate as many complete days as possible within response limits. Quality over quantity."""
                        prompt = self._generate_prompt(trip_request)
                    else:
                        # Retry attempts: Focus on missing days with continued quality
                        previous_days = self._get_previous_days_if_any(trip_request)
                        previous_dates = [day.get('date') for day in previous_days]
                        missing_days = expected_days - len(previous_days)
                        
                        # Generate list of all expected dates
                        from datetime import datetime, timedelta
                        start_date = datetime.strptime(trip_request.get('startDate'), '%Y-%m-%d')
                        end_date = datetime.strptime(trip_request.get('endDate'), '%Y-%m-%d')
                        all_dates = []
                        current_date = start_date
                        while current_date <= end_date:
                            all_dates.append(current_date.strftime('%Y-%m-%d'))
                            current_date += timedelta(days=1)
                        
                        # Find missing dates
                        missing_dates = [date for date in all_dates if date not in previous_dates]
                        
                        system_content = f"""CONTINUATION GENERATION (Retry #{attempt + 1})

CUMULATIVE STRATEGY: You are continuing a travel itinerary generation.

ALREADY GENERATED: {len(previous_days)} days ({', '.join(previous_dates) if previous_dates else 'none'})
NEED TO GENERATE: {len(missing_dates)} more days ({', '.join(missing_dates[:5])}{', ...' if len(missing_dates) > 5 else ''})

CRITICAL: Generate ONLY the missing dates. Do NOT regenerate existing dates.

QUALITY STANDARDS:
- Detailed 2-3 sentence descriptions with specific information
- Accurate preference matching for: {', '.join(trip_request.get('entertainmentPreferences', []))}
- Budget compliance: {trip_request.get('budgetLevel', 'mid-range')}
- At least 1 food activity per day
- Specific venue names and practical details

Generate complete, accurate days for the missing dates only."""
                        prompt = self._generate_quality_focused_retry_prompt(trip_request, attempt, expected_days)

                    logger.info(f"Sending request to {self.provider.upper()} with model {self.model} (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Prompt structure: String prompt")
                    logger.info(f"System message length: {len(system_content)} chars")
                    logger.info(f"User prompt length: {len(prompt)} chars")

                    _debug_log_prompts(attempt, system_content, prompt)

                    # The prompt from _generate_prompt is a single string, not system/user pair
                    # The old call_openai_api took a single prompt string and constructed messages.
                    # The AIClient's direct call to completions.create needs messages.
                    # Let's adjust to ensure messages are built correctly here or in _generate_prompt
                    
                    user_content = prompt # Assuming _generate_prompt returns the user part of the prompt

                    # Get base model config and modify for retry attempts
                    model_config = get_model_config(self.model).copy()
                    if attempt > 0:
                        # AGGRESSIVE RETRY: Respect DeepSeek 8192 token limit
                        model_config['temperature'] = 0.2  # Low temperature for consistency but not too restrictive
                        if self.provider == "deepseek":
                            model_config['max_tokens'] = 6000  # Stay well under DeepSeek 8192 limit for retries
                        else:
                            model_config['max_tokens'] = 12000  # OpenAI can handle higher limits
                        logger.info(f"Retry attempt {attempt + 1}: Using temperature={model_config['temperature']}, max_tokens={model_config['max_tokens']}")
                    else:
                        logger.info(f"First attempt: Using temperature={model_config.get('temperature', 0.3)}, max_tokens={model_config.get('max_tokens', 8000 if self.provider == 'deepseek' else 16000)}")

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
                        logger.error(f"Invalid response structure from {self.provider} API")
                        logger.error(f"Response: {response}")
                        raise ValueError(f"Invalid response structure from {self.provider} API")
                        
                    logger.info(f"Received response from {self.provider.upper()}")
                    
                    content = response.choices[0].message.content
                    if not content:
                        logger.error(f"Empty content in response from {self.provider.upper()} API")
                        logger.error(f"Full response: {response}")
                        raise ValueError(f"Empty content in response from {self.provider.upper()} API")
                    
                    logger.info(f"Response content length: {len(content)} characters")
                    logger.info(f"Response contains {content.count('[DAY_START]')} [DAY_START] blocks")
                    logger.info(f"Response contains {content.count('[DAY_END]')} [DAY_END] blocks")
                    logger.debug(f"First 500 chars of response: {content[:500]}...")
                    
                    _debug_log_response(attempt, content)
                    
                    # ENHANCED DEBUG LOGGING: Analyze response structure
                    _debug_log_response_structure(content, expected_days)

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
                        
                    # ENHANCED TOKEN ANALYSIS: Deep dive into token efficiency
                    _debug_log_token_analysis(token_usage, self.model, self.provider, content)

                    itinerary = await self._process_response(content, trip_request)
                    
                    # Add token usage to the response if available
                    if token_usage:
                        itinerary['token_usage'] = token_usage
                    
                    # Check if processing returned an error response
                    if not itinerary.get('success', True):  # Error responses have success: False
                        logger.warning(f"[PROCESSING ERROR] {itinerary.get('error_type', 'unknown')}: {itinerary.get('message', 'Unknown error')}")
                        
                        # Extract partial data from error response for incomplete responses
                        if itinerary.get('error_type') == 'incomplete_response' and itinerary.get('partial_data'):
                            partial_data = itinerary.get('partial_data', {})
                            partial_days = partial_data.get('days', [])
                            if partial_days:
                                # Store partial result for use in retries
                                partial_cache_key = f"{cache_key}_partial_{attempt}"
                                # Store just the days data for combination
                                partial_result = {'days': partial_days, 'language': partial_data.get('language', 'en')}
                                self.cache[partial_cache_key] = partial_result
                                logger.info(f"[PARTIAL] Stored {len(partial_days)} days from incomplete response (attempt {attempt + 1})")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"[RETRY] Processing error, retrying attempt {attempt + 2}/{max_retries}")
                            continue
                        else:
                            logger.error(f"[FINAL] All {max_retries} attempts had processing errors, checking if we can combine partial results")
                            # Even though all attempts had "processing errors", we might have collected enough days
                            combined_itinerary = self._combine_partial_results(trip_request, expected_days)
                            if combined_itinerary.get('success', True) and len(combined_itinerary.get('days', [])) >= expected_days:
                                logger.info(f"[SUCCESS] Despite processing errors, we collected all {len(combined_itinerary.get('days', []))} days from partial results!")
                                self.cache[cache_key] = combined_itinerary
                                return combined_itinerary
                            else:
                                logger.error(f"[FINAL] Could not combine enough days: {len(combined_itinerary.get('days', []))} out of {expected_days}")
                                return itinerary
                    
                    # Check if response is complete (only for successful responses)
                    actual_days = len(itinerary.get('days', []))
                    
                    if actual_days >= expected_days:
                        logger.info(f"[SUCCESS] Complete itinerary generated with {actual_days} days on attempt {attempt + 1}")
                        if token_usage:
                            logger.info(f"[SUCCESS] Final token cost: {token_usage['total_tokens']} tokens")
                        self.cache[cache_key] = itinerary
                        return itinerary
                    else:
                        # Store partial result for potential combination (only for successful responses)
                        if actual_days > 0:
                            partial_cache_key = f"{cache_key}_partial_{attempt}"
                            self.cache[partial_cache_key] = itinerary
                            logger.info(f"[PARTIAL] Stored {actual_days} days from attempt {attempt + 1}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"[CONTINUE] Got {actual_days}/{expected_days} days on attempt {attempt + 1}, continuing for quality")
                            # Try to combine with previous partial results if available
                            combined_itinerary = self._combine_partial_results(trip_request, expected_days)
                            if combined_itinerary.get('success', True) and len(combined_itinerary.get('days', [])) >= expected_days:
                                logger.info(f"[SUCCESS] Combined partial results into complete itinerary")
                                self.cache[cache_key] = combined_itinerary
                                return combined_itinerary
                            continue
                        else:
                            logger.info(f"[FINAL] Using best available result with {actual_days} days after {max_retries} attempts")
                            # Try to combine all partial results
                            combined_itinerary = self._combine_partial_results(trip_request, expected_days)
                            if combined_itinerary.get('success', True) and len(combined_itinerary.get('days', [])) > actual_days:
                                final_result = combined_itinerary
                            else:
                                # Create final error response for incomplete result
                                final_result = self._create_error_response(
                                    trip_request,
                                    'incomplete_response',
                                    f"After {max_retries} attempts, could only generate {actual_days} out of {expected_days} requested days.",
                                    partial_data=itinerary
                                )
                            return final_result

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
            return self._create_error_response(trip_request, 'generation_failed', str(ve))
        except Exception as e:
            logger.error(f"Error generating itinerary with {self.provider} model {self.model}: {str(e)}", exc_info=True) 
            return self._create_error_response(trip_request, 'generation_failed', str(e))

    def _calculate_expected_days(self, trip_request: Dict[str, Any]) -> int:
        """Calculate the expected number of days for a trip"""
        from datetime import datetime
        start_date = datetime.strptime(trip_request.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(trip_request.get('endDate'), '%Y-%m-%d')
        return (end_date - start_date).days + 1

    def _get_previous_days_if_any(self, trip_request: Dict[str, Any]) -> list:
        """Get any previously generated days from cache to avoid duplication"""
        cache_key = self._generate_cache_key(trip_request)
        all_previous_days = []
        seen_dates = set()
        
        # Check main cache first
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            for day in cached_result.get('days', []):
                date = day.get('date')
                if date and date not in seen_dates:
                    all_previous_days.append(day)
                    seen_dates.add(date)
        
        # Check partial results from previous attempts
        for attempt in range(3):  # max_retries = 3
            partial_key = f"{cache_key}_partial_{attempt}"
            if partial_key in self.cache:
                partial_result = self.cache[partial_key]
                for day in partial_result.get('days', []):
                    date = day.get('date')
                    if date and date not in seen_dates:
                        all_previous_days.append(day)
                        seen_dates.add(date)
        
        # Sort by date to maintain chronological order
        all_previous_days.sort(key=lambda x: x.get('date', ''))
        
        if all_previous_days:
            dates = [day.get('date') for day in all_previous_days]
            logger.info(f"[PREVIOUS DAYS] Found {len(all_previous_days)} previously generated days: {dates}")
        
        return all_previous_days

    def _build_trip_context(self, args: Dict[str, Any]) -> Dict[str, str]:
        """Build reusable trip context information"""
        # Geographic context
        destination = args.get('destination', '').strip()
        origin = args.get('origin', '').strip()
        
        if origin and origin.lower() != 'origin':
            travel_mode = f"{args.get('travelType', 'trip')} from {origin} to {destination}"
            geo_context = f"ROUTE MODE: Plan activities along {origin} → {destination} route. Include stops that make geographic sense for this journey."
            
            # Add distance exclusion if specified
            exclusion_radius = args.get('exclusionRadius')
            exclusion_unit = args.get('exclusionUnit', 'miles')
            
            if exclusion_radius is not None and exclusion_radius >= 0:
                distance_text = f"{exclusion_radius} {exclusion_unit}"
                if exclusion_radius > 0:
                    geo_context += f"\n\nDISTANCE EXCLUSION: Avoid recommending activities within {distance_text} of the starting location ({origin}). Focus on activities that are at least {distance_text} away from the origin point to provide variety and prevent recommendations too close to where the journey begins."
                # else:
                #     geo_context += f"\n\nDISTANCE EXCLUSION: No exclusion radius set ({distance_text}). All activities along the route are acceptable."
        else:
            travel_mode = f"{args.get('travelType', 'trip')} to {destination}"
            geo_context = f"DESTINATION MODE: ALL activities must be within reasonable distance of {destination} area."
            
        # Intermediate stops
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
            
        return {
            'travel_mode': travel_mode,
            'geo_context': geo_context,
            'intermediate_stops_text': intermediate_stops_text
        }
    
    def _build_traveler_info(self, args: Dict[str, Any], compact: bool = False) -> str:
        """Build traveler information string"""
        traveler_info = f"{args.get('adults', 2)} adults"
        if args.get('children', 0) > 0:
            separator = " + " if compact else ", "
            traveler_info += f"{separator}{args.get('children', 0)} children"
        if args.get('infants', 0) > 0:
            separator = " + " if compact else ", "
            traveler_info += f"{separator}{args.get('infants', 0)} infants"
        return traveler_info
    
    def _build_preferences_context(self, args: Dict[str, Any]) -> Dict[str, str]:
        """Build preferences and local focus context"""
        preferences = args.get('entertainmentPreferences', [])
        preferences_text = ', '.join(preferences) if preferences else 'general'
        
        # Hidden gems focus
        local_focus = ""
        if 'hidden-gems' in preferences:
            local_focus = """HIDDEN GEMS - LOCAL FOCUS: Prioritize authentic LOCAL experiences:
- LOCAL favorites: family-run businesses, neighborhood spots popular for locals
- Places where LOCALS go - not tourist traps or chain establishments  
- LOCAL markets, festivals, community centers, family restaurants
- LOCAL-owned shops, artisan workshops, cultural venues"""
            
        return {
            'preferences_text': preferences_text,
            'local_focus': local_focus
        }
    
    def _build_cuisine_instruction(self, args: Dict[str, Any]) -> str:
        """Build cuisine preference instruction"""
        cuisine_preference = args.get('cuisinePreference', 'any')
        if cuisine_preference == 'any':
            return ""
            
        if cuisine_preference == 'local':
            return "Focus on authentic local and traditional restaurants of the region. "
        elif cuisine_preference in ['vegetarian', 'vegan', 'halal', 'kosher']:
            return f"Only suggest {cuisine_preference} restaurants and cafes. Ensure all meal recommendations comply with {cuisine_preference} dietary requirements. "
        elif cuisine_preference == 'international':
            return "Suggest a diverse mix of international restaurants representing various world cuisines. "
        elif cuisine_preference in ['seafood', 'mediterranean', 'asian', 'european', 'american', 'mexican', 'japanese', 'italian', 'slavic', 'indian', 'thai', 'other']:
            return f"Prioritize {cuisine_preference} restaurants and cafes for meal recommendations. When possible, suggest authentic establishments. "
        else:
            return f"Consider {cuisine_preference} cuisine if possible. "
    
    def _get_activity_format_template(self) -> str:
        """Get the standard activity format template"""
        return """FORMAT:
[DAY_START]
Date: YYYY-MM-DD
[ACTIVITY_START]
Time: HH:MM - HH:MM
Type: ONE type only
Price: free/$/$$/$$$ 
Location: Specific venue name, City
Description: 2-3 sentences with details, historical context, practical tips
Why: How this specifically matches preferences and budget
[ACTIVITY_END]
[DAY_END]"""
    
    def _get_quality_requirements(self, preferences_text: str, budget: str, expected_days: int, dates_text: str) -> str:
        """Get standard quality requirements"""
        return f"""QUALITY REQUIREMENTS:
- Target {expected_days} days: {dates_text}
- 3-5 activities per day with detailed descriptions
- MANDATORY: 1+ food activity daily (type "food")
- ALL activities MUST match preferences: {preferences_text}
- ALL activities MUST fit {budget} budget
- ALL activities MUST suit traveler composition
- NO activities that contradict user filters
- 2-3 sentence descriptions with details, context, insider tips
- Explain why each specifically matches {preferences_text} preferences"""
    
    def _get_type_rules(self, preferences_text: str, cuisine_instruction: str) -> str:
        """Get standard type rules"""
        return f"""TYPE RULES:
- Use ONLY ONE type per activity from: {preferences_text} OR food OR must-see OR hidden-gems OR family-friendly
- NEVER combine types (NO "outdoor, family-friendly" - choose ONE)
- Prioritize user preferences: {preferences_text}. {cuisine_instruction}"""

    def _generate_prompt(self, args: Dict[str, Any]) -> str:
        """Generate an efficient prompt with all critical logic preserved"""
        # Calculate expected number of days and format dates
        from datetime import datetime, timedelta
        start_date = datetime.strptime(args.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(args.get('endDate'), '%Y-%m-%d')
        expected_days = (end_date - start_date).days + 1
        
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        dates_text = ', '.join(date_list)

        # Build reusable components
        trip_context = self._build_trip_context(args)
        traveler_info = self._build_traveler_info(args)
        preferences_context = self._build_preferences_context(args)
        cuisine_instruction = self._build_cuisine_instruction(args)
        
        # Build the main prompt
        prompt = f"""Generate a high-quality {expected_days}-day itinerary for {dates_text}

Trip: {trip_context['travel_mode']}{trip_context['intermediate_stops_text']}
{traveler_info} | Budget: {args.get('budgetLevel', 'mid-range')}
Preferences: {preferences_context['preferences_text']}
{trip_context['geo_context']}
{preferences_context['local_focus']}

{self._get_quality_requirements(preferences_context['preferences_text'], args.get('budgetLevel', 'mid-range'), expected_days, dates_text)}

{self._get_type_rules(preferences_context['preferences_text'], cuisine_instruction)}

{self._get_activity_format_template()}

Focus on quality and accuracy. Generate as many complete days as possible within response limits."""

        return prompt

    def _generate_quality_focused_retry_prompt(self, args: Dict[str, Any], attempt: int, expected_days: int) -> str:
        """Generate retry prompt focused on quality and continuation rather than forced completion"""
        from datetime import datetime, timedelta
        start_date = datetime.strptime(args.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(args.get('endDate'), '%Y-%m-%d')
        
        # Get already generated days to avoid duplication
        previous_days = self._get_previous_days_if_any(args)
        generated_dates = [day.get('date') for day in previous_days]
        
        # Generate all required dates
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Identify missing dates
        missing_dates = [date for date in all_dates if date not in generated_dates]
        
        # Build context using helper methods
        preferences_context = self._build_preferences_context(args)
        traveler_info = self._build_traveler_info(args, compact=True)
        
        # Simplified geographic context for retry
        destination = args.get('destination', '').strip()
        origin = args.get('origin', '').strip()
        if origin and origin.lower() != 'origin':
            geo_context = f"ROUTE: Activities along {origin} → {destination} journey"
            
            # Add distance exclusion for retry prompts
            exclusion_radius = args.get('exclusionRadius')
            exclusion_unit = args.get('exclusionUnit', 'miles')
            
            if exclusion_radius is not None and exclusion_radius >= 0:
                distance_text = f"{exclusion_radius} {exclusion_unit}"
                if exclusion_radius > 0:
                    geo_context += f" | AVOID activities within {distance_text} of {origin}"
                else:
                    geo_context += f" | No exclusion radius ({distance_text})"
        else:
            geo_context = f"DESTINATION: Activities near {destination} only"

        local_note = "Focus on authentic LOCAL experiences where LOCALS go" if 'hidden-gems' in preferences_context['preferences_text'] else ""
        
        if missing_dates:
            # Limit to first 5 missing dates to avoid overwhelming the AI
            dates_to_generate = missing_dates[:5]
            continuation_text = f"GENERATE THESE SPECIFIC DATES ONLY: {', '.join(dates_to_generate)}"
            
            if len(missing_dates) > 5:
                continuation_text += f"\n(Focus on first {len(dates_to_generate)} dates. Do NOT generate all {len(missing_dates)} missing dates in one response.)"
        else:
            continuation_text = f"ERROR: No missing dates found. All {expected_days} days already generated: {', '.join(all_dates)}"

        retry_prompt = f"""{continuation_text}

{geo_context} | {traveler_info} | {args.get('budgetLevel', 'mid-range')}
Preferences: {preferences_context['preferences_text']}
{local_note}

CONTINUATION RULES:
- Generate ONLY the specific dates listed above
- Do NOT regenerate any existing dates: {', '.join(generated_dates) if generated_dates else 'none generated yet'}
- Match user preferences: {preferences_context['preferences_text']}
- Fit budget: {args.get('budgetLevel', 'mid-range')}
- Include 1+ food activity daily (type "food")
- 2-3 sentence descriptions with specific details
- ONE type per activity only

FORMAT (Use exact dates specified above):
[DAY_START]
Date: YYYY-MM-DD (from the specific dates list above)
[ACTIVITY_START]
Time: HH:MM - HH:MM
Type: ONE from: {preferences_context['preferences_text']} OR food OR must-see OR hidden-gems OR family-friendly
Price: free/$/$$/$$$ 
Location: Specific venue name, City
Description: 2-3 sentences with details, context, tips
Why: How this matches {preferences_context['preferences_text']} and budget
[ACTIVITY_END]
[DAY_END]

CRITICAL: Only generate the specific dates requested. Quality over quantity."""

        return retry_prompt

    async def _process_response(self, response: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process the response from the AI model"""
        # Define regex patterns as constants for readability and reuse
        RE_DAY_DATE = re.compile(r'Date: (\d{4}-\d{2}-\d{2})')
        RE_ACTIVITY_BLOCKS = re.compile(r'(\[ACTIVITY_START\].*?(?=\n\s*\[ACTIVITY_START\]|\n\s*\[DAY_END\]|$))', re.DOTALL)
        RE_TIME = re.compile(r'Time:\s*(.+?)\n')
        RE_TYPE = re.compile(r'Type:\s*([^,\n]+)(?:,.*?)?\s*\n', re.IGNORECASE)  # Captures first type before comma or newline
        RE_PRICE = re.compile(r'Price:\s*(free|\$|\$\$|\$\$\$)\s*\n', re.IGNORECASE)
        RE_LOCATION = re.compile(r'Location:\s*(.*?)(?=\n\s*(?:Why:|Price:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)
        RE_DESCRIPTION = re.compile(r'Description:\s*(.*?)(?=\n\s*(?:Why:|Price:|Location:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)
        RE_WHY = re.compile(r'Why:\s*(.*?)(?=\n\s*(?:Price:|Location:|Description:|Type:|Time:|\[ACTIVITY_END\]|$))', re.DOTALL | re.IGNORECASE)

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
                    activity_data = {}
                    
                    time_match = RE_TIME.search(activity_text)
                    activity_data['time'] = time_match.group(1).strip() if time_match else "Time not specified"
                    
                    type_match = RE_TYPE.search(activity_text)
                    if type_match:
                        raw_type = type_match.group(1).strip().lower()
                        # Normalize type to preference-based categories
                        type_mapping = {
                            'lunch': 'food',
                            'dining': 'food', 
                            'restaurant': 'food',
                            'meal': 'food',
                            'sightseeing': 'must-see',
                            'attraction': 'must-see',
                            'landmark': 'must-see',
                            'activity': 'outdoor',  # Default fallback
                            'accommodation': 'travel',
                            'travel': 'travel'
                        }
                        activity_type_str = type_mapping.get(raw_type, raw_type)
                    else:
                        activity_type_str = 'activity'
                    activity_data['type'] = activity_type_str
                    
                    price_match = RE_PRICE.search(activity_text)
                    activity_data['price'] = price_match.group(1) if price_match else '$$'
                    
                    location_match = RE_LOCATION.search(activity_text)
                    activity_data['location'] = location_match.group(1).strip() if location_match else "Location not specified"
                    
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
                
                # Return warning response with partial data instead of proceeding
                partial_itinerary = {'days': days, 'language': args.get('language', 'en')}
                return self._create_error_response(
                    args, 
                    'incomplete_response', 
                    f"AI generated only {len(days)} out of {expected_days} requested days. This often happens with longer trips due to token limits.",
                    partial_data=partial_itinerary
                )

            logger.info(f"[DEBUG] Successfully processed {len(days)} days out of {expected_days} expected")
            
            return {
                'success': True,
                'days': days,
                'language': args.get('language', 'en')
            }

        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}", exc_info=True)
            return self._create_error_response(args, 'processing_error', str(e))

    def _validate_response(self, response: str, args: Dict[str, Any]) -> bool:
        """Validate the response format and content. Returns True if valid, False otherwise."""
        try:
            logger.info(f"[VALIDATION DEBUG] === STARTING RESPONSE VALIDATION ===")
            logger.info(f"[VALIDATION DEBUG] Response length: {len(response)} characters")
            
            if not response.strip():
                logger.error("[VALIDATION DEBUG] AI response is empty.")
                return False

            required_tags = ['[DAY_START]', '[ACTIVITY_START]']
            missing_tags = [tag for tag in required_tags if tag not in response]
            if missing_tags:
                logger.error(f"[VALIDATION DEBUG] Missing required tags: {missing_tags}")
                logger.error(f"[VALIDATION DEBUG] Available tags: {[tag for tag in required_tags if tag in response]}")
                return False
            
            logger.info(f"[VALIDATION DEBUG] Found required tags: {required_tags}")
            
            # Check for date pattern
            date_pattern = r'Date: \d{4}-\d{2}-\d{2}'
            date_matches = re.findall(date_pattern, response)
            if not date_matches:
                logger.error("[VALIDATION DEBUG] No valid 'Date: YYYY-MM-DD' found in response.")
                logger.error(f"[VALIDATION DEBUG] Looking for pattern: {date_pattern}")
                # Show first 500 chars to see what format we actually got
                logger.error(f"[VALIDATION DEBUG] First 500 chars: {response[:500]}")
                return False
            else:
                logger.info(f"[VALIDATION DEBUG] Found {len(date_matches)} valid dates: {date_matches}")

            try:
                target_language = args.get('language', 'en')
                logger.info(f"[VALIDATION DEBUG] Target language: {target_language}")
                
                if target_language == 'en':
                    logger.info(f"[VALIDATION DEBUG] English language validation - passed")
                    return True

                desc_samples = re.findall(r'Description:\s*(.*?)(?=\n\s*(?:Why:|$))', response, re.DOTALL | re.IGNORECASE)
                sample_text = ' '.join(s.strip() for s in desc_samples if s.strip())[:500]
                
                logger.info(f"[VALIDATION DEBUG] Description samples found: {len(desc_samples)}")
                logger.info(f"[VALIDATION DEBUG] Sample text length: {len(sample_text)}")
                
                if sample_text:
                    detected_lang = detect(sample_text)
                    lang_map = {'en': ['en'], 'es': ['es'], 'fr': ['fr'], 'de': ['de'], 'it': ['it'], 'ru': ['ru'], 'zh': ['zh-cn', 'zh-tw']}
                    
                    expected_langs = lang_map.get(target_language, [target_language])
                    logger.info(f"[VALIDATION DEBUG] Language detection - detected: {detected_lang}, expected: {expected_langs}")
                    
                    if detected_lang not in expected_langs:
                        logger.warning(f"[VALIDATION DEBUG] Language mismatch. Expected {target_language} (one of {expected_langs}), detected {detected_lang}")
                    else:
                        logger.info(f"[VALIDATION DEBUG] Language validation passed")
                else:
                    logger.warning(f"[VALIDATION DEBUG] No sample text available for language detection")
                    
            except Exception as lang_e:
                logger.warning(f"[VALIDATION DEBUG] Language detection failed: {str(lang_e)}")

            logger.info(f"[VALIDATION DEBUG] === VALIDATION PASSED ===")
            return True

        except Exception as e:
            logger.error(f"[VALIDATION DEBUG] Unexpected error during validation: {str(e)}", exc_info=True)
            return False
            
    def _create_error_response(self, trip_data: Dict[str, Any], error_type: str, message: str, partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create proper error/warning response instead of misleading fallback itinerary"""
        logger.error(f"Creating {error_type} response for {trip_data.get('destination', 'Unknown')}: {message}")
        
        response = {
            'success': False,
            'error_type': error_type,  # 'generation_failed', 'incomplete_response', 'processing_error'
            'message': message,
            'destination': trip_data.get('destination', 'Unknown'),
            'language': trip_data.get('language', 'en'),
            'requested_days': self._calculate_expected_days(trip_data),
            'partial_data': partial_data or {}
        }
        
        # Add specific guidance based on error type
        if error_type == 'generation_failed':
            response['suggestions'] = [
                'Try selecting different entertainment preferences',
                'Consider a shorter trip duration',
                'Try a different destination',
                'Check if the destination name is spelled correctly'
            ]
        elif error_type == 'incomplete_response':
            response['suggestions'] = [
                'Try reducing the trip duration',
                'Simplify entertainment preferences',
                'Use a more popular destination',
                'Try generating again - sometimes it works on retry'
            ]
            if partial_data and partial_data.get('days'):
                response['partial_days_received'] = len(partial_data['days'])
        elif error_type == 'processing_error':
            response['suggestions'] = [
                'Please try again in a few moments',
                'Check your internet connection',
                'If the problem persists, contact support'
            ]
        
        return response

    async def refresh_activity_suggestion(
        self,
        original_activity: dict,
        custom_preferences: str,
        activity_type: str,
        is_meal: bool
    ) -> Dict[str, Any]:
        """
        Generates a new activity suggestion to replace an existing one, using AI.
        Now includes caching to reduce redundant API calls.
        """
        try:
            # Check cache first to avoid redundant API calls
            cache_key = self._generate_activity_cache_key(original_activity, custom_preferences, activity_type, is_meal)
            
            if cache_key in self.cache:
                logger.info(f"[CACHE HIT] Using cached activity refresh result")
                return self.cache[cache_key]
            
            logger.info(f"[CACHE MISS] Generating new activity via API call")
            
            prompt = f'''
            Generate a new activity to replace:
            {original_activity.get('description')}
            
            IMPORTANT: Use this EXACT format:
            [ACTIVITY_START]
            Time: {original_activity.get('time')}
            Type: {activity_type}
            Description: (new activity description)
            Why: Explanation of why this activity is recommended
            Price: free|$|$$|$$$
            Location: Specific place name
            [ACTIVITY_END]

            Rules:
            1. Keep the same time slot: {original_activity.get('time')}
            2. Keep similar type of activity and use the same responselanguage
            3. Make it family-friendly and engaging
            4. Include specific details and locations
            5. For the Location field, provide the exact name of the place (restaurant, museum, park, etc.)
            '''

            if custom_preferences:
                prompt += f'''
            User's custom preferences: {custom_preferences}
            '''
            
            if 'hidden-gems' in custom_preferences.lower():
                prompt += '''
            HIDDEN GEMS FOCUS: Generate lesser-known, authentic local experiences:
            - Avoid mainstream tourist spots
            - Focus on local favorites with high ratings but low tourist traffic
            - Include authentic neighborhood gems and family-run establishments
            '''
            
            if is_meal:
                prompt += '''
            For meal activities, provide 2-3 specific restaurant options with brief descriptions
            Format the description exactly like this: 
            "Options include: 
            1. Restaurant Name - Brief description of cuisine and ambiance. 
            2. Restaurant Name - Brief description. 
            3. Restaurant Name - Brief description."
            
            IMPORTANT: Make sure each numbered restaurant option is on its own line, and use proper spacing.
            Do NOT split restaurant names across multiple lines.
            '''

            model_config = get_model_config(self.model)
            logger.debug(f"AIClient: Refreshing activity with model {self.model}, provider {self.provider}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel activity generator. Generate a single new activity using the exact format provided. It should be the same city as the original activity. For meal activities, always suggest 2-3 specific restaurant options with brief descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **model_config
            )
            
            content = response.choices[0].message.content
            logger.debug(f"AIClient: Raw AI response for refresh: {content}")
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            new_activity = {
                'time': original_activity.get('time'),
                'type': activity_type
            }
            
            current_field = None
            description_lines = []

            for line in lines:
                if line == "[ACTIVITY_START]" or line == "[ACTIVITY_END]":
                    continue

                if line.startswith('Time: '):
                    new_activity['time'] = line.replace('Time: ', '').strip()
                    current_field = None
                elif line.startswith('Type: '):
                    new_activity['type'] = line.replace('Type: ', '').strip().lower()
                    current_field = None
                elif line.startswith('Description: '):
                    description_lines.append(line.replace('Description: ', '').strip())
                    current_field = 'description'
                elif line.startswith('Why: '):
                    if description_lines and current_field == 'description':
                         new_activity['description'] = "\n".join(description_lines)
                         description_lines = []
                    new_activity['why'] = line.replace('Why: ', '').strip()
                    current_field = None
                elif line.startswith('Price: '):
                    if description_lines and current_field == 'description':
                         new_activity['description'] = "\n".join(description_lines)
                         description_lines = []
                    new_activity['price'] = line.replace('Price: ', '').strip()
                    current_field = None
                elif line.startswith('Location: '):
                    if description_lines and current_field == 'description':
                         new_activity['description'] = "\n".join(description_lines)
                         description_lines = []
                    new_activity['location'] = line.replace('Location: ', '').strip()
                    current_field = None
                elif current_field == 'description':
                    description_lines.append(line)
                elif is_meal and re.match(r"^\d+\.", line) and description_lines and current_field == 'description':
                    description_lines.append(line)

            if description_lines:
                new_activity['description'] = "\n".join(description_lines)

            if not new_activity.get('description'):
                logger.error("AIClient: No description generated for new activity during refresh.")
                raise ValueError("No description generated for new activity")
            
            # Cache the result for future use
            self.cache[cache_key] = new_activity
            logger.info(f"[CACHE STORE] Cached activity refresh result")
            
            logger.info(f"AIClient: Successfully generated new activity: {json.dumps(new_activity, indent=2)}")
            return new_activity

        except Exception as e:
            logger.error(f"AIClient: Error refreshing activity: {str(e)}", exc_info=True)
            raise

    def _combine_partial_results(self, trip_request: Dict[str, Any], expected_days: int) -> Dict[str, Any]:
        """Combine partial results from multiple attempts to form a complete itinerary"""
        from datetime import datetime, timedelta
        
        cache_key = self._generate_cache_key(trip_request)
        combined_days = []
        seen_dates = set()
        
        # Collect all partial results from attempts
        for attempt in range(3):  # max_retries = 3
            partial_key = f"{cache_key}_partial_{attempt}"
            if partial_key in self.cache:
                partial_result = self.cache[partial_key]
                for day in partial_result.get('days', []):
                    date = day.get('date')
                    if date and date not in seen_dates:
                        combined_days.append(day)
                        seen_dates.add(date)
                        logger.info(f"[COMBINE] Added day {date} from attempt {attempt}")
        
        # Sort days by date
        combined_days.sort(key=lambda x: x.get('date', ''))
        
        # Generate expected dates for validation
        start_date = datetime.strptime(trip_request.get('startDate'), '%Y-%m-%d')
        end_date = datetime.strptime(trip_request.get('endDate'), '%Y-%m-%d')
        expected_dates = []
        current_date = start_date
        while current_date <= end_date:
            expected_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Check coverage
        found_dates = [day.get('date') for day in combined_days]
        missing_dates = set(expected_dates) - set(found_dates)
        
        logger.info(f"[COMBINE] Combined {len(combined_days)} days from partial results")
        logger.info(f"[COMBINE] Expected: {len(expected_dates)} days, Found: {len(found_dates)} days")
        
        if missing_dates:
            logger.info(f"[COMBINE] Missing dates: {sorted(missing_dates)}")
        
        if len(combined_days) > 0:
            combined_result = {
                'success': True,
                'days': combined_days,
                'language': trip_request.get('language', 'en'),
                'partial_combination': True,
                'missing_dates': sorted(missing_dates) if missing_dates else []
            }
            return combined_result
        else:
            logger.warning("[COMBINE] No partial results found to combine")
            return self._create_error_response(trip_request, 'incomplete_response', "No valid days found in AI response")

    def _validate_day_quality(self, day: dict) -> bool:
        """Ensure each day has minimum quality standards"""
        activities = day.get('activities', [])
        has_food = any(act.get('type') == 'food' for act in activities)
        min_activities = len(activities) >= 3
        return has_food and min_activities

__all__ = ['AIClient']

