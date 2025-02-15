from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

class BudgetLevel(str, Enum):
    budget = "budget"
    mid_range = "mid_range"
    luxury = "luxury"

class TripDetails(BaseModel):
    travel_type: str
    departure: str
    destination: str
    start_date: date
    end_date: date
    num_adults: int = Field(..., ge=1)
    num_children: Optional[int] = 0
    num_infants: Optional[int] = 0
    intermediate_stops: Optional[List[str]] = []

class Activity(BaseModel):
    time: str
    description: str

class DailyItinerary(BaseModel):
    date: date
    activities: List[Activity]
    backups: Optional[List[Activity]] = []

class TripItinerary(BaseModel):
    trip_id: str
    itinerary: List[DailyItinerary]
    hotels: Optional[List[str]] = []
    generated_at: datetime

class TripCreate(BaseModel):
    userId: str
    formData: Dict[str, Any]
    itinerary: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "userId": "123",
                "formData": {
                    "destination": "Paris",
                    "startDate": "2024-03-01",
                    "endDate": "2024-03-07"
                },
                "itinerary": {
                    "days": []
                }
            }
        }

class TripRequest(BaseModel):
    trip_details: TripDetails
    preferences: dict
    budget: dict
    ai_model: dict
    language: str = "en"

class TripResponse(BaseModel):
    id: str
    userId: str
    formData: Dict[str, Any]
    itinerary: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 