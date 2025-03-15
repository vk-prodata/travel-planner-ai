# backend/models.py
# This file imports from the models directory for backward compatibility

from .models import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripHash,
    Activity,
    DailyItinerary,
    TripItinerary,
    TripRequest
)

# Re-export the TripHash class for backward compatibility
class TripHashCompat(TripHash):
    pass 