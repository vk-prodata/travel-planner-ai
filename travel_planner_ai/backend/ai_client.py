# backend/ai_client.py
import os
import openai
from functools import wraps
from cachetools import TTLCache, cached
from travel_planner_ai.backend.models import TripRequest
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file

openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your environment

# Create a TTL cache with a maximum of 100 items and TTL of 1 hour.
ai_cache = TTLCache(maxsize=100, ttl=3600)

def ai_provider_decorator(provider):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if provider == "GPT-4o":
                return func(*args, **kwargs)
            elif provider == "Gemini":
                # TODO: Implement Gemini integration using its SDK or API.
                raise NotImplementedError("Gemini integration not implemented yet")
            else:
                raise ValueError("Unknown AI provider")
        return wrapper
    return decorator

def generate_cache_key(trip_request: TripRequest) -> str:
    # Use the JSON representation of the trip_request as a unique key.
    return trip_request.json()

@cached(cache=ai_cache, key=generate_cache_key)
@ai_provider_decorator("GPT-4o")
def generate_itinerary_with_openai(trip_request: TripRequest):
    prompt = (
        f"Generate a detailed travel itinerary in {trip_request.language} for a trip from "
        f"{trip_request.trip_details.departure} to {trip_request.trip_details.destination} starting on "
        f"{trip_request.trip_details.start_date} and ending on {trip_request.trip_details.end_date}. "
        f"Consider these preferences: {trip_request.preferences.dict()}. "
        f"Budget: {trip_request.budget.level}. "
        f"Include recommendations for hotels and local activities for {trip_request.trip_details.num_adults} adults, "
        f"{trip_request.trip_details.num_children} children, and {trip_request.trip_details.num_infants} infants. "
        f"Also, consider intermediate stops: {trip_request.trip_details.intermediate_stops}."
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # Default AI model
        messages=[
            {"role": "system", "content": "You are an expert travel planner."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    
    itinerary_text = response.choices[0].message.content
    # TODO: Parse itinerary_text into a structured TripItinerary.
    # For now, return a dummy itinerary.
    from datetime import datetime, timedelta
    import uuid
    days = (trip_request.trip_details.end_date - trip_request.trip_details.start_date).days + 1
    itinerary = []
    for day in range(days):
        current_date = trip_request.trip_details.start_date + timedelta(days=day)
        itinerary.append({
            "date": str(current_date),
            "activities": [{"time": "09:00 AM", "description": "Sample activity based on prompt"}],
            "backups": [{"time": "10:00 AM", "description": "Backup activity"}]
        })
    
    return {
        "trip_id": str(uuid.uuid4()),
        "itinerary": itinerary,
        "hotels": ["Hotel A", "Hotel B"],  # TODO: Implement dynamic hotel recommendations.
        "generated_at": str(datetime.utcnow())
    }
