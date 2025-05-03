from typing import Dict

AI_CONFIG = {
    "default_model": "gpt-3.5-turbo-16k",  # Using a stable model as default
    "models": {
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
            "frequency_penalty": 0.1,   # discourage repeated phrasing in “description”/“why”
            "presence_penalty": 0.0    # keep encouraging new content where needed
        },
        "gpt-4": {  # Configuration for gpt-4
            "max_tokens": 4096, # Example value, adjust as needed
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    }
}

def get_model_config(model_name: str = None) -> Dict:
    """Get configuration for specified model or default model"""
    model = model_name or AI_CONFIG["default_model"]
    if model not in AI_CONFIG["models"]:
        model = AI_CONFIG["default_model"]
    return AI_CONFIG["models"][model] 