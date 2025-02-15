from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from ..auth import get_current_user
from ..models import TripCreate, Trip
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/trips")
async def create_trip(
    trip_data: TripCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Creating trip for user: {current_user['email']}")
        
        # Add user_id to trip data
        trip_dict = trip_data.dict()
        trip_dict["user_id"] = current_user["id"]
        
        # Insert into MongoDB
        result = db.trips_collection.insert_one(trip_dict)
        logger.info(f"Trip created with ID: {result.inserted_id}")
        
        # Return created trip
        created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        created_trip["_id"] = str(created_trip["_id"])
        
        return created_trip
    except Exception as e:
        logger.error(f"Error creating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 