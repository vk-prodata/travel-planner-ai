# backend/trip_planner.py
from models import TripRequest, TripItinerary
from ai_client import generate_itinerary_with_openai

def generate_itinerary(trip_request: TripRequest) -> TripItinerary:
    itinerary_data = generate_itinerary_with_openai(trip_request)
    return TripItinerary(**itinerary_data)
