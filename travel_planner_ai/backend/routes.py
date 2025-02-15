# backend/routes.py
from fastapi import APIRouter, HTTPException, Depends
from .models import TripCreate, TripResponse, TripRequest  # Add TripRequest back
from .database import get_trips_collection, get_db
from .auth import get_current_user
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/trips")
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        # Access current_user as a dictionary
        if trip.userId != current_user['id']:
            raise HTTPException(
                status_code=403,
                detail="User ID mismatch"
            )

        trip_dict = trip.dict()
        trip_dict["user_id"] = current_user['id']  # Use dictionary access
        trip_dict["created_at"] = datetime.now()
        trip_dict["updated_at"] = datetime.now()
        
        logger.info(f"Creating trip for user: {current_user['email']}")
        result = db.trips_collection.insert_one(trip_dict)
        
        created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        if created_trip:
            created_trip["_id"] = str(created_trip["_id"])
            return created_trip
        else:
            raise HTTPException(status_code=404, detail="Trip not found after creation")
            
    except Exception as e:
        logger.error(f"Error creating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trips/user/{user_id}", response_model=list[TripResponse])
async def get_user_trips(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' trips")
    
    try:
        trips = list(db.trips_collection.find({"user_id": user_id}))
        return [
            {
                **trip,
                "id": str(trip["_id"]),
                "_id": str(trip["_id"])
            } for trip in trips
        ]
    except Exception as e:
        logger.error(f"Error fetching trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/trips/{trip_id}")
async def update_trip(
    trip_id: str,
    trip: TripCreate,  # Change to TripCreate instead of TripRequest
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        existing_trip = db.trips_collection.find_one({"_id": ObjectId(trip_id)})
        if not existing_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if existing_trip["user_id"] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this trip")
        
        update_data = trip.dict()
        update_data["updated_at"] = datetime.now()
        
        result = db.trips_collection.update_one(
            {"_id": ObjectId(trip_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_trip = db.trips_collection.find_one({"_id": ObjectId(trip_id)})
            updated_trip["_id"] = str(updated_trip["_id"])
            return updated_trip
        raise HTTPException(status_code=400, detail="Failed to update trip")
    except Exception as e:
        logger.error(f"Error updating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))
