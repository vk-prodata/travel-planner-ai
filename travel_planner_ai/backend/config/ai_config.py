from typing import Dict

AI_CONFIG = {
    "default_model": "gpt-4o-2024-11-20", #"gpt-4o-2024-11-20",  # Using a stable model as default
    "deepseek_default_model": "deepseek-chat", # DeepSeek default model
    "models": {
        "gpt-4o-2024-11-20vk": {
            "max_tokens": 12000,
            "temperature": 0.3,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.0,
            "stop": ["### END"]
        },
        "gpt-3.5-turbo": {  # Primary model config
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        },
        "gpt-3.5-turbo-16k": {  # Primary model config
            "max_tokens": 12000,      # covers ~4 000 tokens of response + buffer
            "temperature": 0.3,      # low randomness for consistent JSON structure
            "top_p":      0.9,       # nucleus sampling to prune very unlikely tokens
            "frequency_penalty": 0.1,   # discourage repeated phrasing in "description"/"why"
            "presence_penalty": 0.0    # keep encouraging new content where needed
        },
        "gpt-3.5-turbo-16k-new": {  # Primary model config
            "max_tokens": 12000,        # plenty for ~4k tokens of output + buffer
            "temperature": 0.5,         # more creative, so it fills in real activities
            "top_p": 1.0,               # sample from full distribution
            "frequency_penalty": 0.2,   # discourage repeated "fallback" phrasing
            "presence_penalty": 0.1     # nudge toward introducing new content
        },
        "gpt-4-turbo-8k": {
            "max_tokens": 8000,
            "temperature": 0.5,
            "top_p": 1.0,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1
        },
        "gpt-4": {  # Configuration for gpt-4
            "max_tokens": 4096, # Example value, adjust as needed
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        },
        "gpt-4o-2024-11-20": {
            "temperature": 0.3,    # Low temperature for consistency and correctness in format (reduces hallucinations while keeping some creativity).
            "top_p": 1.0,          # Use full token distribution; primary randomness control via temperature.
            "max_tokens": 8000,    # Allow up to ~6000 tokens in the response (covers detailed itineraries up to 10 days).
            "frequency_penalty": 0.0,  # No repetition penalty (itineraries may naturally repeat structure like days of week).
            "presence_penalty": 0.0,   # No presence penalty (avoid forcing new/unrelated content; focus on relevant activities).
        },
        # DeepSeek model configurations
        "deepseek-chat": {
            "temperature": 0.4,    # Slightly higher than OpenAI for creativity while maintaining coherence
            "top_p": 0.95,         # Slightly reduced nucleus sampling to maintain focus
            "max_tokens": 6000,    # Similar to OpenAI to handle detailed itineraries
            "frequency_penalty": 0.1,  # Small penalty to reduce repetition
            "presence_penalty": 0.1,   # Small penalty to encourage diverse content
        },
        "deepseek-coder": {  # Alternative model with more structured output
            "temperature": 0.3,    # Lower temperature for more consistent formatting
            "top_p": 0.9,          # Further reduced for consistency
            "max_tokens": 6000,    # Same token limit
            "frequency_penalty": 0.2,  # Higher penalty to avoid repetitive suggestions
            "presence_penalty": 0.0,   # No presence penalty to maintain focus
        }
    }
}

def get_model_config(model_name: str = None) -> Dict:
    """Get configuration for specified model or default model"""
    model = model_name or AI_CONFIG["default_model"]
    
    # Handle DeepSeek models that might not be in the config
    if model.startswith("deepseek-") and model not in AI_CONFIG["models"]:
        # If we have a DeepSeek model that's not explicitly configured,
        # use the default DeepSeek config
        return AI_CONFIG["models"]["deepseek-chat"]
    
    # For other models not in config, use the default model config
    if model not in AI_CONFIG["models"]:
        model = AI_CONFIG["default_model"]
        
    return AI_CONFIG["models"][model] 