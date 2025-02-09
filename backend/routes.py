# backend/routes.py
from fastapi import APIRouter, HTTPException
from models import TripRequest, TripItinerary
from trip_planner import generate_itinerary
from db import save_trip, get_trip

router = APIRouter()

@router.post("/generate-trip", response_model=TripItinerary)
async def generate_trip_endpoint(trip_request: TripRequest):
    try:
        trip_itinerary = generate_itinerary(trip_request)
        trip_data = trip_itinerary.dict()
        saved_trip = await save_trip(trip_data)
        if not saved_trip:
            raise HTTPException(status_code=500, detail="Failed to save trip")
        return trip_itinerary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trip/{trip_id}", response_model=TripItinerary)
async def fetch_trip(trip_id: str):
    trip = await get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
