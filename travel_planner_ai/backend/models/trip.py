from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
from enum import Enum
import hashlib
import uuid

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

class TripHash(BaseModel):
    userId: str
    origin: str
    destination: str
    startDate: str
    endDate: str

    def generate_hash(self) -> str:
        # Create a deterministic string from trip details
        hash_string = f"{self.userId}:{self.origin}:{self.destination}:{self.startDate}:{self.endDate}"
        # Generate SHA-256 hash
        return hashlib.sha256(hash_string.encode()).hexdigest()

class TripCreate(BaseModel):
    userId: str
    formData: Dict[str, Any]
    itinerary: Optional[Dict[str, Any]] = None

    @field_validator('formData')
    def validate_form_data(cls, v):
        required_fields = ['destination', 'startDate', 'endDate']
        for field in required_fields:
            if field not in v or not v[field]:
                raise ValueError(f"Missing required field: {field}")
        return v

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )

class TripUpdate(BaseModel):
    userId: Optional[str] = None
    formData: Optional[Dict[str, Any]] = None
    itinerary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
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
    )

class TripRequest(BaseModel):
    trip_details: TripDetails
    preferences: dict
    budget: dict
    ai_model: dict
    language: str = "en"

class TripResponse(BaseModel):
    id: str
    user_id: str
    formData: Dict[str, Any]
    itinerary: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Trip(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    ) 