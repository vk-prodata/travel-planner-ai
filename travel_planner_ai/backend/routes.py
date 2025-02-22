# backend/routes.py
from fastapi import APIRouter, HTTPException, Depends
from .models import TripCreate, TripResponse, TripHash
from .database import get_db
from .auth import get_current_user
from datetime import datetime
from bson import ObjectId
import logging
import uuid
from .ai.base_client import BaseAIClient
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize AI client
ai_client = BaseAIClient(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/trips")
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        # Generate trip hash
        trip_hash = TripHash(
            userId=current_user['id'],
            origin=trip.formData.get('origin', ''),
            destination=trip.formData['destination'],
            startDate=trip.formData['startDate'],
            endDate=trip.formData['endDate']
        ).generate_hash()

        # Check if trip with this hash exists
        existing_trip = db.trips_collection.find_one({"trip_hash": trip_hash})
        if existing_trip:
            raise HTTPException(
                status_code=409,
                detail="A similar trip already exists"
            )

        # Create trip with hash
        trip_dict = trip.dict()
        trip_id = str(uuid.uuid4())
        trip_dict.update({
            "_id": ObjectId(),
            "id": trip_id,
            "trip_hash": trip_hash,
            "user_id": current_user['id'],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        # Remove redundant fields
        trip_dict.pop('userId', None)  # Remove old userId field
        if 'tripId' in trip_dict.get('itinerary', {}):
            trip_dict['itinerary']['tripId'] = trip_id  # Update itinerary tripId
        
        logger.info(f"""
        Creating new trip:
        - Trip ID: {trip_id}
        - User: {current_user['email']}
        - Destination: {trip_dict.get('formData', {}).get('destination')}
        - Created at: {trip_dict['created_at']}
        """)
        
        result = db.trips_collection.insert_one(trip_dict)
        
        created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        if created_trip:
            created_trip["_id"] = str(created_trip["_id"])
            logger.info(f"Successfully created trip with ID: {trip_id}")
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
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        # Try to find by MongoDB _id first
        try:
            existing_trip = db.trips_collection.find_one({"_id": ObjectId(trip_id)})
        except:
            # If not a valid ObjectId, try finding by our application id
            existing_trip = db.trips_collection.find_one({"id": trip_id})
            
        if not existing_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if existing_trip["user_id"] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this trip")
        
        # Prepare update data with consistent ID fields
        update_data = trip.dict()
        update_data.update({
            "user_id": current_user['id'],
            "id": existing_trip.get('id') or trip_id,
            "updated_at": datetime.now()
        })
        
        # Remove redundant fields
        update_data.pop('userId', None)
        if 'tripId' in update_data.get('itinerary', {}):
            update_data['itinerary']['tripId'] = trip_id

        logger.info(f"""
        Updating trip:
        - Trip ID: {trip_id}
        - User: {current_user['email']}
        - Destination: {update_data.get('formData', {}).get('destination')}
        - Updated at: {update_data['updated_at']}
        - Itinerary changes: {update_data.get('itinerary')}
        """)
        
        # Use the correct _id for the update
        mongo_id = existing_trip['_id']
        result = db.trips_collection.update_one(
            {"_id": mongo_id},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_trip = db.trips_collection.find_one({"_id": mongo_id})
            updated_trip["_id"] = str(updated_trip["_id"])
            logger.info(f"Successfully updated trip with ID: {trip_id}")
            return updated_trip
        
        logger.info(f"No changes made to trip with ID: {trip_id}")
        existing_trip["_id"] = str(existing_trip["_id"])
        return existing_trip
        
    except Exception as e:
        logger.error(f"Error updating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-itinerary")
async def generate_itinerary(
    trip_request: TripCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Generate itinerary using AI
        itinerary = ai_client.generate_itinerary(trip_request.formData)
        
        # Return the generated itinerary
        return {
            "success": True,
            "itinerary": itinerary
        }
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
