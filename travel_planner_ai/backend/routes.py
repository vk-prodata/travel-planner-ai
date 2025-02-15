# backend/routes.py
from fastapi import APIRouter, HTTPException, Depends
from .models import TripRequest, TripResponse
from .database import get_trips_collection
from .auth import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/trips", response_model=TripResponse)
async def create_trip(trip: TripRequest, current_user = Depends(get_current_user)):
    if trip.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create trips for other users")
    
    collection = get_trips_collection()
    trip_dict = trip.model_dump()
    trip_dict["_id"] = str(ObjectId())
    trip_dict["created_at"] = datetime.now()
    trip_dict["updated_at"] = datetime.now()
    
    try:
        await collection.insert_one(trip_dict)
        return {**trip_dict, "id": trip_dict["_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/trips/user/{user_id}", response_model=list[TripResponse])
async def get_user_trips(user_id: str, current_user = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' trips")
    
    collection = get_trips_collection()
    try:
        trips = await collection.find({"userId": user_id}).to_list(None)
        return [{**trip, "id": trip["_id"]} for trip in trips]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, trip: TripRequest, current_user = Depends(get_current_user)):
    collection = get_trips_collection()
    
    try:
        existing_trip = await collection.find_one({"_id": trip_id})
        if not existing_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if existing_trip["userId"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this trip")
        
        update_data = trip.model_dump()
        update_data["updated_at"] = datetime.now()
        
        result = await collection.update_one(
            {"_id": trip_id},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_trip = await collection.find_one({"_id": trip_id})
            return {**updated_trip, "id": updated_trip["_id"]}
        raise HTTPException(status_code=400, detail="Failed to update trip")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
