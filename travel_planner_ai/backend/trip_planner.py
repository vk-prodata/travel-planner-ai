# backend/trip_planner.py
from travel_planner_ai.backend.models import TripRequest, TripItinerary
from travel_planner_ai.backend.ai_client import generate_itinerary_with_openai

def generate_itinerary(trip_request: TripRequest) -> TripItinerary:
    itinerary_data = generate_itinerary_with_openai(trip_request)
    return TripItinerary(**itinerary_data)
