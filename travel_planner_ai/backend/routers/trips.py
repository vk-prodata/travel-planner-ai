from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db, get_user_collection
from ..auth import get_current_user
from ..models import TripCreate, TripUpdate
from bson import ObjectId
import logging
import datetime
from ..services.credits_service import deduct_credits, deduct_credits_for_trip

logger = logging.getLogger(__name__)

router = APIRouter()

def normalize_trip_data(trip):
    """Ensure trip data has consistent structure for frontend compatibility."""
    if not trip:
        logger.warning("Attempted to normalize None trip data")
        return None
        
    # Create a copy to avoid modifying the original
    normalized_trip = dict(trip)
    
    # Ensure _id is converted to string
    if "_id" in normalized_trip:
        normalized_trip["_id"] = str(normalized_trip["_id"])
    
    # Add id field for consistency if it doesn't exist
    if "id" not in normalized_trip:
        normalized_trip["id"] = str(normalized_trip.get("_id", ""))
    
    # Ensure itinerary exists and has a valid structure
    if "itinerary" not in normalized_trip or not normalized_trip["itinerary"]:
        logger.warning(f"Trip {normalized_trip.get('id')} is missing itinerary, creating empty one")
        normalized_trip["itinerary"] = {"days": []}
    elif isinstance(normalized_trip["itinerary"], dict) and "days" not in normalized_trip["itinerary"]:
        logger.warning(f"Trip {normalized_trip.get('id')} itinerary is missing days array, adding empty one")
        normalized_trip["itinerary"]["days"] = []
    elif not isinstance(normalized_trip["itinerary"], dict):
        logger.error(f"Trip {normalized_trip.get('id')} has invalid itinerary type: {type(normalized_trip['itinerary'])}")
        normalized_trip["itinerary"] = {"days": []}
    else:
        # Ensure days is a list
        if not isinstance(normalized_trip["itinerary"]["days"], list):
            logger.error(f"Trip {normalized_trip.get('id')} has invalid days type: {type(normalized_trip['itinerary']['days'])}")
            normalized_trip["itinerary"]["days"] = []
        else:
            logger.debug(f"Trip {normalized_trip.get('id')} has {len(normalized_trip['itinerary']['days'])} days in itinerary")
    
    # Convert datetime objects to ISO format strings
    for field in ["created_at", "updated_at"]:
        if field in normalized_trip:
            if isinstance(normalized_trip[field], datetime.datetime):
                normalized_trip[field] = normalized_trip[field].isoformat()
    
    # Ensure formData exists
    if "formData" not in normalized_trip:
        logger.warning(f"Trip {normalized_trip.get('id')} is missing formData")
        normalized_trip["formData"] = {}
    elif not isinstance(normalized_trip["formData"], dict):
        logger.error(f"Trip {normalized_trip.get('id')} has invalid formData type: {type(normalized_trip['formData'])}")
        normalized_trip["formData"] = {}
    
    # Ensure language is set in formData
    if "formData" in normalized_trip and isinstance(normalized_trip["formData"], dict):
        if "language" not in normalized_trip["formData"]:
            logger.warning(f"Trip {normalized_trip.get('id')} formData is missing language, defaulting to English")
            normalized_trip["formData"]["language"] = "en"
    
    # Log the structure of the normalized trip
    logger.debug(f"Normalized trip {normalized_trip.get('id')} structure: {list(normalized_trip.keys())}")
    
    return normalized_trip

@router.get("/trips")
async def get_user_trips(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Fetching trips for user: {current_user['email']}")
        
        # Find all trips for the current user
        trips = list(db.trips_collection.find({"user_id": current_user["id"]}))
        
        # Normalize all trips
        normalized_trips = [normalize_trip_data(trip) for trip in trips]
        
        logger.info(f"Found {len(normalized_trips)} trips")
        return normalized_trips
        
    except Exception as e:
        logger.error(f"Error fetching trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Fetching trip {trip_id} for user: {current_user['email']}")
        
        # First try direct UUID match without user_id constraint
        trip = db.trips_collection.find_one({
            "id": trip_id
        })
        
        logger.debug(f"Direct UUID search result: {trip is not None}")
        
        # If not found, try with ObjectId without user_id constraint
        if not trip:
            try:
                logger.debug(f"Trying ObjectId search for {trip_id}")
                trip = db.trips_collection.find_one({
                    "_id": ObjectId(trip_id)
                })
                logger.debug(f"ObjectId search result: {trip is not None}")
            except Exception as e:
                logger.warning(f"Could not convert {trip_id} to ObjectId: {e}")
        
        if not trip:
            logger.warning(f"Trip {trip_id} not found in database")
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Add a flag to indicate if the current user is the owner
        normalized_trip = normalize_trip_data(trip)
        normalized_trip["isOwner"] = trip.get("user_id") == current_user["id"]
        
        # Ensure itinerary is properly included
        if not normalized_trip.get("itinerary"):
            logger.warning(f"Trip {trip_id} has no itinerary, creating empty one")
            normalized_trip["itinerary"] = {"days": []}
        
        # Log the structure of the trip being returned
        logger.info(f"Found trip {trip_id} with keys: {list(normalized_trip.keys())}")
        logger.debug(f"Itinerary structure: {normalized_trip.get('itinerary', {}).keys()}")
        
        return normalized_trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trip {trip_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching trip: {str(e)}")

@router.post("/trips")
async def create_trip(
    trip_data: TripCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
    users_collection = Depends(get_user_collection)
):
    try:
        logger.info(f"Creating trip for user: {current_user['email']}")
        logger.debug(f"Trip data received: {trip_data}")
        
        # Check if the trip already has an itinerary, which would indicate 
        # credits were already deducted during itinerary generation
        should_deduct_credits = True
        if hasattr(trip_data, "itinerary") and trip_data.itinerary and trip_data.itinerary.get("days"):
            days_count = len(trip_data.itinerary.get("days", []))
            if days_count > 0:
                logger.info(f"Trip already has an itinerary with {days_count} days, skipping credit deduction")
                should_deduct_credits = False
        
        # Deduct credits based on trip days only if needed
        user_id = current_user["id"]
        if should_deduct_credits:
            try:
                credits_result = deduct_credits_for_trip(users_collection, user_id, trip_data)
                logger.info(f"Credits deducted successfully for user {user_id}. Remaining credits: {credits_result.get('available_credits', 'N/A')}")
            except HTTPException as credit_error:
                # Re-raise the exception to send appropriate error response to frontend
                raise credit_error
        else:
            logger.info(f"Skipping credit deduction for user {user_id} as they likely already paid for itinerary generation")
            
        # Convert Pydantic model to dict and add user_id
        trip_dict = trip_data.dict()
        trip_dict["user_id"] = user_id
        
        # Validate and ensure itinerary is included
        if "itinerary" not in trip_dict or not trip_dict["itinerary"]:
            logger.warning("No itinerary found in trip data, creating empty one")
            trip_dict["itinerary"] = {"days": []}
        elif "days" not in trip_dict["itinerary"]:
            logger.warning("Itinerary missing 'days' field, adding empty days array")
            trip_dict["itinerary"]["days"] = []
            
        # Validate and ensure formData is included
        if "formData" not in trip_dict or not trip_dict["formData"]:
            logger.error("No formData found in trip data")
            raise HTTPException(status_code=400, detail="Missing formData in trip data")
            
        # Ensure language is included in formData
        if "language" not in trip_dict["formData"]:
            logger.warning("No language found in formData, defaulting to English")
            trip_dict["formData"]["language"] = "en"
            
        # Log the structure of the trip being saved
        logger.debug(f"Trip structure before saving: {list(trip_dict.keys())}")
        if "itinerary" in trip_dict:
            logger.debug(f"Itinerary structure: {list(trip_dict['itinerary'].keys())}")
            if "days" in trip_dict["itinerary"]:
                logger.debug(f"Itinerary has {len(trip_dict['itinerary']['days'])} days")
        
        # Add timestamps if MongoDB doesn't do it automatically
        now = datetime.datetime.utcnow()
        if "created_at" not in trip_dict:
            trip_dict["created_at"] = now
        if "updated_at" not in trip_dict:
            trip_dict["updated_at"] = trip_dict.get("created_at", now)
        
        # Insert into MongoDB
        result = db.trips_collection.insert_one(trip_dict)
        logger.info(f"Trip created with ID: {result.inserted_id}")
        
        # Verify the trip was saved correctly
        created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        if not created_trip:
            logger.error(f"Failed to retrieve created trip with ID: {result.inserted_id}")
            raise HTTPException(status_code=500, detail="Failed to retrieve created trip")
            
        # Check if itinerary was saved
        if "itinerary" not in created_trip or not created_trip["itinerary"]:
            logger.error(f"Itinerary not saved for trip with ID: {result.inserted_id}")
            
            # Try to update the trip with the itinerary
            update_result = db.trips_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"itinerary": trip_dict["itinerary"]}}
            )
            logger.info(f"Attempted to fix missing itinerary: {update_result.modified_count} documents modified")
            
            # Retrieve the trip again
            created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        
        # Return created trip
        normalized_trip = normalize_trip_data(created_trip)
        
        # Verify the normalized trip has the itinerary
        if not normalized_trip.get("itinerary"):
            logger.error(f"Normalized trip is missing itinerary: {normalized_trip.keys()}")
        else:
            logger.info(f"Trip created successfully with itinerary containing {len(normalized_trip['itinerary'].get('days', []))} days")
        
        return normalized_trip
    except Exception as e:
        logger.error(f"Error creating trip: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/trips/{trip_id}")
async def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Updating trip {trip_id} for user: {current_user['email']}")
        logger.debug(f"Trip update data received: {trip_data}")
        
        # Validate trip ID
        try:
            object_id = ObjectId(trip_id)
        except:
            logger.error(f"Invalid trip ID format: {trip_id}")
            raise HTTPException(status_code=400, detail="Invalid trip ID format")
        
        # Check if trip exists and belongs to user
        existing_trip = db.trips_collection.find_one({"_id": object_id, "user_id": current_user["id"]})
        if not existing_trip:
            logger.error(f"Trip {trip_id} not found or does not belong to user {current_user['id']}")
            raise HTTPException(status_code=404, detail="Trip not found or does not belong to user")
        
        # Convert Pydantic model to dict
        update_data = trip_data.dict(exclude_unset=True)
        
        # Log the structure of the update data
        logger.debug(f"Update data structure: {list(update_data.keys())}")
        
        # Validate and ensure itinerary is included
        if "itinerary" in update_data:
            if not update_data["itinerary"]:
                logger.warning("Empty itinerary in update data, using existing itinerary")
                update_data["itinerary"] = existing_trip.get("itinerary", {"days": []})
            elif "days" not in update_data["itinerary"]:
                logger.warning("Itinerary missing 'days' field, adding empty days array")
                update_data["itinerary"]["days"] = []
            else:
                logger.info(f"Updating itinerary with {len(update_data['itinerary'].get('days', []))} days")
        else:
            logger.warning("No itinerary in update data, keeping existing itinerary")
            # Don't modify the existing itinerary if not provided in update
        
        # Validate and ensure formData is included
        if "formData" in update_data:
            if not update_data["formData"]:
                logger.warning("Empty formData in update data, using existing formData")
                update_data["formData"] = existing_trip.get("formData", {})
            
            # Ensure language is included in formData
            if "language" not in update_data["formData"]:
                logger.warning("No language found in formData update, keeping existing or defaulting to English")
                update_data["formData"]["language"] = existing_trip.get("formData", {}).get("language", "en")
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.datetime.utcnow()
        
        # Update in MongoDB
        result = db.trips_collection.update_one(
            {"_id": object_id, "user_id": current_user["id"]},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            logger.warning(f"No changes made to trip {trip_id}")
        else:
            logger.info(f"Trip {trip_id} updated successfully")
        
        # Verify the trip was updated correctly
        updated_trip = db.trips_collection.find_one({"_id": object_id})
        if not updated_trip:
            logger.error(f"Failed to retrieve updated trip with ID: {trip_id}")
            raise HTTPException(status_code=500, detail="Failed to retrieve updated trip")
            
        # Check if itinerary was saved
        if "itinerary" in update_data and ("itinerary" not in updated_trip or not updated_trip["itinerary"]):
            logger.error(f"Itinerary not saved for trip with ID: {trip_id}")
            
            # Try to update the trip with the itinerary again
            retry_result = db.trips_collection.update_one(
                {"_id": object_id},
                {"$set": {"itinerary": update_data["itinerary"]}}
            )
            logger.info(f"Attempted to fix missing itinerary: {retry_result.modified_count} documents modified")
            
            # Retrieve the trip again
            updated_trip = db.trips_collection.find_one({"_id": object_id})
        
        # Return updated trip
        normalized_trip = normalize_trip_data(updated_trip)
        
        # Verify the normalized trip has the itinerary
        if "itinerary" in update_data and not normalized_trip.get("itinerary"):
            logger.error(f"Normalized trip is missing itinerary after update: {normalized_trip.keys()}")
        else:
            logger.info(f"Trip updated successfully with itinerary containing {len(normalized_trip.get('itinerary', {}).get('days', []))} days")
        
        return normalized_trip
    except Exception as e:
        logger.error(f"Error updating trip: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trips/{trip_id}")
async def delete_trip(
    trip_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        logger.info(f"Deleting trip {trip_id} for user: {current_user['email']}")
        
        # Try to find trip by id first
        trip = db.trips_collection.find_one({
            "id": trip_id,
            "user_id": current_user["id"]
        })
        
        # If not found, try with ObjectId
        if not trip:
            try:
                trip = db.trips_collection.find_one({
                    "_id": ObjectId(trip_id),
                    "user_id": current_user["id"]
                })
            except Exception as e:
                logger.warning(f"Could not convert {trip_id} to ObjectId: {e}")
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Delete the trip - try both id formats
        if "id" in trip and trip["id"] == trip_id:
            result = db.trips_collection.delete_one({
                "id": trip_id,
                "user_id": current_user["id"]
            })
        else:
            try:
                result = db.trips_collection.delete_one({
                    "_id": ObjectId(trip_id),
                    "user_id": current_user["id"]
                })
            except Exception as e:
                logger.error(f"Error deleting trip: {e}")
                raise HTTPException(status_code=400, detail="Invalid trip ID format")
            
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        logger.info(f"Trip {trip_id} deleted successfully")
        return {"message": "Trip deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trip: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 