from typing import Dict

AI_CONFIG = {
    "default_model": "gpt-3.5-turbo",  # Using a stable model as default
    "models": {
        "gpt-3.5-turbo": {  # Primary model config
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
        model = AI_CONFIG["default_model"]
    return AI_CONFIG["models"][model] 