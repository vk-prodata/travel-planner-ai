from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class Activity(BaseModel):
    id: str
    time: str
    description: str
    type: str

class Day(BaseModel):
    date: str
    activities: List[Activity]

class TripItinerary(BaseModel):
    tripId: str
    days: List[Day]

class TripRequest(BaseModel):
    userId: str
    itinerary: TripItinerary
    formData: Dict

class TripResponse(BaseModel):
    id: str
    userId: str
    itinerary: TripItinerary
    formData: Dict
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now() 