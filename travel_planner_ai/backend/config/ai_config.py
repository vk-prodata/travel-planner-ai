from typing import Dict

AI_CONFIG = {
    "default_model": "o3-mini",  # Primary model
    "models": {
        "o3-mini": {  # Primary model config
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        },
        "gpt-3.5-turbo": {  # Fallback model config
            "max_tokens": 2000,
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
        # If requested model not found, use default
        model = AI_CONFIG["default_model"]
        # If default also not found, use fallback
        if model not in AI_CONFIG["models"]:
            model = "o3-mini" #"gpt-3.5-turbo"
    return AI_CONFIG["models"][model] 