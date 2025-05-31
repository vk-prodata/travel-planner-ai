from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from datetime import date, datetime, timedelta
from enum import Enum
import hashlib
import uuid

class BudgetLevel(str, Enum):
    budget = "budget"
    mid_range = "mid_range"
    luxury = "luxury"

class Activity(BaseModel):
    id: Optional[str] = None  # TODO: Deprecated Activity ID June 2025 - no longer generated or used
    time: str
    description: str
    type: str
    location: Optional[str] = None
    coordinates: Optional[str] = None  # TODO: Deprecated Coordinates June 2025 - no longer generated or used for maps
    priceLevel: Optional[str] = None
    why: Optional[str] = None

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
        # Also ensure dates are in correct format
        try:
            if 'startDate' in v and v['startDate']:
                date.fromisoformat(v['startDate'])
            if 'endDate' in v and v['endDate']:
                date.fromisoformat(v['endDate'])
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        return v

    @model_validator(mode='after')
    def check_trip_duration(self) -> 'TripCreate':
        form_data = self.formData
        if form_data and 'startDate' in form_data and 'endDate' in form_data:
            try:
                start_date_str = form_data['startDate']
                end_date_str = form_data['endDate']

                if not start_date_str or not end_date_str: # Skip if either is empty, covered by field_validator
                    return self

                start_date = date.fromisoformat(start_date_str)
                end_date = date.fromisoformat(end_date_str)

                if start_date > end_date:
                    raise ValueError("End date cannot be earlier than start date.")

                if (end_date - start_date).days > 10:
                    raise ValueError("Trip duration cannot exceed 10 days.")
            except ValueError as e: # Catch specific ValueError for date parsing or our custom messages
                raise ValueError(str(e)) # Re-raise to be caught by FastAPI
            except Exception as e: # Catch any other unexpected errors during date processing
                # Log this error for debugging, as it's unexpected
                print(f"Unexpected error during date validation: {e}") # Or use a proper logger
                raise ValueError("An unexpected error occurred while validating trip dates.")
        return self

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

    @model_validator(mode='after')
    def check_trip_duration_update(self) -> 'TripUpdate':
        form_data = self.formData
        if form_data and 'startDate' in form_data and 'endDate' in form_data:
            # This validator relies on both dates being present.
            # If only one is provided during an update, this check might not be appropriate
            # or needs to be adjusted based on how partial updates are handled.
            # For now, we assume if formData is present, both dates relevant for duration check are also present if being changed.
            start_date_str = form_data.get('startDate')
            end_date_str = form_data.get('endDate')

            if start_date_str and end_date_str: # Only proceed if both dates are provided in the update
                try:
                    start_date = date.fromisoformat(start_date_str)
                    end_date = date.fromisoformat(end_date_str)

                    if start_date > end_date:
                        raise ValueError("End date cannot be earlier than start date.")
                    if (end_date - start_date).days > 10:
                        raise ValueError("Trip duration cannot exceed 10 days.")
                except ValueError as e: # Catch specific ValueError for date parsing or our custom messages
                    raise ValueError(str(e)) # Re-raise to be caught by FastAPI
                except Exception as e: # Catch any other unexpected errors
                    print(f"Unexpected error during date validation on update: {e}") # Or use a proper logger
                    raise ValueError("An unexpected error occurred while validating trip dates on update.")
        return self

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