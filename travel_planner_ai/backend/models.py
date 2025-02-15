# backend/models.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

class BudgetLevel(str, Enum):
    budget = "budget"
    mid_range = "mid_range"
    luxury = "luxury"

class TripDetails(BaseModel):
    travel_type: str  # e.g., "road_trip", "flight", "train", "cruise"
    departure: str
    destination: str
    start_date: date
    end_date: date
    num_adults: int = Field(..., ge=1)
    num_children: Optional[int] = 0  # Ages 2-12
    num_infants: Optional[int] = 0   # Under 2
    intermediate_stops: Optional[List[str]] = []  # Extra cities/places to stay

class Preferences(BaseModel):
    outdoor: bool = False
    cultural: bool = False
    relaxation: bool = False
    family_friendly: bool = False
    food_tours: bool = False

class BudgetPreferences(BaseModel):
    level: BudgetLevel

class AIModelSelection(BaseModel):
    model: str  # e.g., "GPT-4o", "Gemini", "DeepSeek"

class TripRequest(BaseModel):
    trip_details: TripDetails
    preferences: Preferences
    budget: BudgetPreferences
    ai_model: AIModelSelection
    language: str = "en"  # UI remains English for now

class Activity(BaseModel):
    time: str  # e.g., "09:00 AM"
    description: str

class DailyItinerary(BaseModel):
    date: date
    activities: List[Activity]
    backups: Optional[List[Activity]] = []

class TripItinerary(BaseModel):
    trip_id: str
    itinerary: List[DailyItinerary]
    hotels: Optional[List[str]] = []  # Hotel recommendations
    generated_at: datetime

class TripCreate(BaseModel):
    userId: str
    formData: dict
    itinerary: dict

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
