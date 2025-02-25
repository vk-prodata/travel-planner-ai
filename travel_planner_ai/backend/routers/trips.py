from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from ..auth import get_current_user
from ..models import TripCreate, Trip
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/trips")
async def get_user_trips(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Fetching trips for user: {current_user['email']}")
        
        # Find all trips for the current user
        trips = list(db.trips_collection.find({"user_id": current_user["id"]}))
        
        # Convert ObjectId to string and ensure itinerary exists
        for trip in trips:
            trip["_id"] = str(trip["_id"])
            if "itinerary" not in trip:
                trip["itinerary"] = {}  # Use empty dictionary instead of None
        
        logger.info(f"Found {len(trips)} trips")
        return trips
        
    except Exception as e:
        logger.error(f"Error fetching trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.delete("/trips/{trip_id}")
async def delete_trip(
    trip_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Deleting trip {trip_id} for user: {current_user['email']}")
        
        # Check if trip exists and belongs to user
        trip = db.trips_collection.find_one({
            "_id": ObjectId(trip_id),
            "user_id": current_user["id"]
        })
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Delete the trip
        result = db.trips_collection.delete_one({
            "_id": ObjectId(trip_id),
            "user_id": current_user["id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        logger.info(f"Trip {trip_id} deleted successfully")
        return {"message": "Trip deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting trip: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 