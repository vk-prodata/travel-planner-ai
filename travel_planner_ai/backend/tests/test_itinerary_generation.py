import os
from dotenv import load_dotenv
from typing import Dict
from travel_planner_ai.backend.ai.base_client import BaseAIClient

def get_model_config(model_name: str = None) -> Dict:
    """
    Returns configuration for specified model or the default model.
    """
    model = model_name or AI_CONFIG["default_model"]
    return AI_CONFIG["models"][model]

def test_real_itinerary_generation():
    """
    Test function that attempts to generate an itinerary using the BaseAIClient.
    """
    load_dotenv()
    client = BaseAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    
    test_prompt = {
        "origin": "Florida",
        "destination": "Tampa",
        "startDate": "2025-04-16",
        "endDate": "2025-04-17",
        "travelType": "car",
        "adults": 2,
        "children": 2,
        "infants": 0,
        "budgetLevel": "mid-range",
        "entertainmentPreferences": ["cultural", "food", "beaches"],
        "intermediateStops": []
    }

    try:
        print(f"\n=== Attempting Itinerary Generation with {client.model} ===")
        result = client.generate_itinerary(test_prompt)
        print_itinerary_result(result)
        return True

    except Exception as e:
        msg = str(e)
        print(f"[ERROR] Failed to generate itinerary with {client.model}: {msg}")
        return False

def print_itinerary_result(result: dict):
    """Helper function to nicely print the itinerary result."""
    print("\n=== Generated Itinerary ===")
    print(f"Success: {result['success']}")
    print(f"Generated at: {result['generated_at']}")
    print("\nContent:")
    print(result['content'])

if __name__ == "__main__":
    test_real_itinerary_generation()