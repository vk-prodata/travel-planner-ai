# backend/models.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum
import hashlib

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

class TripUpdate(BaseModel):
    userId: Optional[str] = None
    formData: Optional[dict] = None
    itinerary: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "formData": {
                    "destination": "Paris",
                    "startDate": "2024-03-01",
                    "endDate": "2024-03-07",
                    "language": "en"
                },
                "itinerary": {
                    "days": []
                }
            }
        }

class TripResponse(BaseModel):
    id: str
    user_id: str
    formData: dict
    itinerary: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123",
                "user_id": "456",
                "formData": {
                    "destination": "Paris",
                    "startDate": "2024-03-01",
                    "endDate": "2024-03-07"
                },
                "itinerary": {
                    "days": []
                },
                "created_at": "2024-03-01T00:00:00",
                "updated_at": "2024-03-01T00:00:00"
            }
        }

class TripHash:
    def __init__(self, userId: str, destination: str, startDate: str, endDate: str, origin: str = ""):
        self.userId = userId
        self.destination = destination.lower().strip()
        self.startDate = startDate
        self.endDate = endDate
        self.origin = origin.lower().strip() if origin else ""
    
    def generate_hash(self) -> str:
        """Generate a hash based on user ID, destination, and date range"""
        # Create a string with all the components
        hash_string = f"{self.userId}:{self.destination}:{self.startDate}:{self.endDate}"
        if self.origin:
            hash_string += f":{self.origin}"
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(hash_string.encode())
        return hash_obj.hexdigest()
