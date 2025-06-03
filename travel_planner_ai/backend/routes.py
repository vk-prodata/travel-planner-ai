# backend/routes.py
from fastapi import APIRouter, HTTPException, Depends, status
from .models import TripCreate, TripResponse, TripHash
from .database import get_db
from .auth import get_current_user
from datetime import datetime
from bson import ObjectId
import logging
import uuid
from .ai_client import AIClient
from .config.ai_config import get_model_config
import os
from typing import Optional
from pathlib import Path
import json
from pydantic import BaseModel
from .services.credits_service import deduct_credits, deduct_credits_for_trip
from .database import get_user_collection

# Set up file logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / f"travel_planner_{datetime.now().strftime('%Y%m%d')}.log")
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

router = APIRouter()

# Initialize AI client
ai_client = AIClient(api_key=os.getenv("OPENAI_API_KEY"))

class RefreshActivityRequest(BaseModel):
    day_index: int
    activity_index: int
    activity: dict
    custom_preferences: str = ""

@router.post("/trips")
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    users_collection = Depends(get_user_collection)
):
    try:
        # Check if we need to deduct credits - handle both 'id' and '_id' field names
        user_id = current_user.get('id') or current_user.get('_id')
        user_email = current_user.get('email', 'unknown')
        should_deduct_credits = True
        
        # If the trip already has an itinerary, assume credits were already deducted during itinerary generation
        if trip.itinerary and trip.itinerary.get('days') and len(trip.itinerary.get('days', [])) > 0:
            logger.info(f"[routes.py] Trip already has an itinerary, assuming credits were deducted during generation")
            should_deduct_credits = False
        
        # Deduct credits only if necessary
        if should_deduct_credits:
            try:
                logger.info(f"[routes.py] Processing credit deduction for user {user_id}")
                credits_result = deduct_credits(users_collection, user_id, 1)
                logger.info(f"[routes.py] Credit deduction successful. Remaining credits: {credits_result.get('available_credits', 'N/A')}")
            except HTTPException as credit_error:
                # Re-raise the exception to send appropriate error response to frontend
                logger.warning(f"[routes.py] Credit deduction failed: {credit_error.detail}")
                raise credit_error
        
        logger.info(f"""
        Starting trip creation process:
        - User: {user_email} (ID: {user_id})
        - Destination: {trip.formData.get('destination')}
        - Date Range: {trip.formData.get('startDate')} to {trip.formData.get('endDate')}
        - Has Itinerary: {bool(trip.itinerary)}
        - Itinerary Days: {len(trip.itinerary.get('days', []))}
        """)
        
        # Normalize destination name (lowercase, strip whitespace)
        destination = trip.formData.get('destination', '')
        trip.formData['destination'] = destination.strip()
        
        # Generate trip hash
        trip_hash = TripHash(
            userId=user_id,
            origin=trip.formData.get('origin', ''),
            destination=trip.formData['destination'],
            startDate=trip.formData['startDate'],
            endDate=trip.formData['endDate']
        ).generate_hash()
        
        logger.info(f"Generated trip hash: {trip_hash}")

        # Check if trip with this hash exists
        existing_trip = db.trips_collection.find_one({"trip_hash": trip_hash})
        if existing_trip:
            logger.warning(f"Trip with hash {trip_hash} already exists (ID: {existing_trip.get('id')})")
            
            # Check if the user wants to update the existing trip
            update_existing = trip.formData.get('updateExisting', False)
            
            if update_existing:
                logger.info(f"Updating existing trip instead of creating new one")
                
                # Update the existing trip
                trip_dict = trip.dict()
                trip_dict.pop('userId', None)  # Remove old userId field
                
                # Keep the original ID and created_at
                trip_id = existing_trip['id']
                if 'tripId' in trip_dict.get('itinerary', {}):
                    trip_dict['itinerary']['tripId'] = trip_id
                
                # Update the trip
                db.trips_collection.update_one(
                    {"_id": ObjectId(existing_trip['_id'])},
                    {"$set": {
                        "formData": trip_dict['formData'],
                        "itinerary": trip_dict['itinerary'],
                        "updated_at": datetime.now()
                    }}
                )
                
                # Return the updated trip
                updated_trip = db.trips_collection.find_one({"_id": ObjectId(existing_trip['_id'])})
                if updated_trip:
                    updated_trip["_id"] = str(updated_trip["_id"])
                    logger.info(f"Successfully updated trip with ID: {trip_id}")
                    return updated_trip
            else:
                # For all trips, return the conflict error
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
            "user_id": user_id,
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
        - User: {user_email} (ID: {user_id})
        - Destination: {trip_dict.get('formData', {}).get('destination')}
        - Created at: {trip_dict['created_at']}
        - Itinerary structure: {list(trip_dict.get('itinerary', {}).keys())}
        - Itinerary days: {len(trip_dict.get('itinerary', {}).get('days', []))}
        """)
        
        # Log the full trip data for debugging
        logger.debug(f"Full trip data: {json.dumps(trip_dict, default=str)}")
        
        result = db.trips_collection.insert_one(trip_dict)
        logger.info(f"MongoDB insert result: {result.inserted_id}")
        
        created_trip = db.trips_collection.find_one({"_id": result.inserted_id})
        if created_trip:
            created_trip["_id"] = str(created_trip["_id"])
            logger.info(f"Successfully created trip with ID: {trip_id}")
            return created_trip
        else:
            logger.error(f"Trip not found after creation with ID: {trip_id}")
            raise HTTPException(status_code=404, detail="Trip not found after creation")
            
    except HTTPException as he:
        logger.error(f"HTTP exception in create_trip: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error creating trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating trip: {str(e)}")

@router.get("/trips/user/{user_id}", response_model=list[TripResponse])
async def get_user_trips(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Handle both 'id' and '_id' field names
    current_user_id = current_user.get('id') or current_user.get('_id')
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view other users' trips")
    
    try:
        trips = list(db.trips_collection.find({"user_id": user_id}))
        
        # Ensure all trips have the required fields for TripResponse
        formatted_trips = []
        for trip in trips:
            # Convert ObjectId to string
            trip["id"] = str(trip["_id"])
            trip["_id"] = str(trip["_id"])
            
            # Ensure itinerary field exists
            if "itinerary" not in trip:
                trip["itinerary"] = {"tripId": trip["id"], "days": []}
                
            formatted_trips.append(trip)
            
        return formatted_trips
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
        # Handle both 'id' and '_id' field names
        current_user_id = current_user.get('id') or current_user.get('_id')
        user_email = current_user.get('email', 'unknown')
        
        # Try to find by MongoDB _id first
        try:
            existing_trip = db.trips_collection.find_one({"_id": ObjectId(trip_id)})
        except:
            # If not a valid ObjectId, try finding by our application id
            existing_trip = db.trips_collection.find_one({"id": trip_id})
            
        if not existing_trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        if existing_trip["user_id"] != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this trip")
        
        # Prepare update data with consistent ID fields
        update_data = trip.dict()
        update_data.update({
            "user_id": current_user_id,
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
        - User: {user_email}
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
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    try:
        # Handle both 'id' and '_id' field names
        user_id = current_user.get('id') or current_user.get('_id')
        user_email = current_user.get('email', 'unknown')
        logger.info(f"Generating itinerary for user {user_id} ({user_email})")
        
        # Log request data
        logger.info(f"Request data: {json.dumps(trip_request.formData, indent=2)}")
        
        # Get AI provider from request or default to OpenAI
        ai_provider = trip_request.formData.get('aiProvider', 'openai')
        logger.info(f"Using AI provider: {ai_provider}")
        
        # Deduct credits based on trip days
        try:
            credits_result = deduct_credits_for_trip(users_collection, user_id, trip_request)
            logger.info(f"Credits deducted for itinerary generation. Remaining: {credits_result.get('available_credits', 'N/A')}")
        except HTTPException as credit_error:
            # Re-raise the exception to send appropriate error response to frontend
            raise credit_error

        # Generate itinerary using AI with the specified provider
        try:
            # Force the AI client to use the specified provider
            ai_client.set_provider(ai_provider)
            
            # Add userId to formData for cache key generation
            form_data_with_user = trip_request.formData.copy()
            form_data_with_user['userId'] = user_id
            
            itinerary = await ai_client.generate_itinerary(form_data_with_user)
            
            # Log raw AI response
            logger.debug(f"Raw AI response: {json.dumps(itinerary, indent=2)}")
            
            if not itinerary or not isinstance(itinerary, dict):
                logger.error(f"Invalid AI response format: {itinerary}")
                raise ValueError("Invalid response from AI service")
            
            # Check if AI client returned an error response
            if not itinerary.get('success', True):
                logger.warning(f"AI generation warning/error: {itinerary.get('error_type')}: {itinerary.get('message')}")
                return {
                    "success": False,
                    "error_type": itinerary.get('error_type'),
                    "message": itinerary.get('message'),
                    "suggestions": itinerary.get('suggestions', []),
                    "destination": itinerary.get('destination'),
                    "requested_days": itinerary.get('requested_days'),
                    "partial_data": itinerary.get('partial_data', {}),
                    "partial_days_received": itinerary.get('partial_days_received')
                }
            
            # Ensure the response has the correct structure for successful responses
            if not itinerary.get('days'):
                logger.error("No days found in itinerary")
                return {
                    "success": False,
                    "error_type": "processing_error",
                    "message": "AI generated response without any trip days",
                    "suggestions": [
                        "Try a different destination",
                        "Simplify your preferences",
                        "Try generating again"
                    ]
                }

            # Format each day's activities
            for day in itinerary['days']:
                if not day.get('activities'):
                    day['activities'] = []
                for activity in day['activities']:
                    if not activity.get('time'):
                        activity['time'] = "9:00 AM"
                    if not activity.get('description'):
                        activity['description'] = "No content generated"
                    if not activity.get('type'):
                        activity['type'] = "activity"
                    # TODO: Deprecated Activity ID June 2025 - activity ID fallback generation no longer needed
                    # if not activity.get('id'):
                    #     activity['id'] = f"{day['date']}-{id(activity)}"

            logger.info(f"Successfully formatted itinerary for {user_email} using {ai_provider} provider")
            logger.debug(f"Final formatted itinerary: {json.dumps(itinerary, indent=2)}")
            
            # Add tripId and isOwner flag
            itinerary['tripId'] = f"temp-{datetime.now().timestamp()}"
            itinerary['isOwner'] = True
            
            return {
                "success": True,
                "itinerary": itinerary
            }
            
        except Exception as e:
            logger.error(f"Error generating itinerary with {ai_provider} provider: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dear {user_email}, we encountered an error with {ai_provider} provider: {str(e)}"
            )

    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dear {current_user.get('email', 'unknown')}, an unexpected error occurred"
        )

@router.delete("/activities/{day_index}/{activity_index}")
async def delete_activity(
    day_index: int,
    activity_index: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Deleting activity {activity_index} from day {day_index} for user {current_user.get('email')}")
        
        # Simply return success since the frontend handles the actual deletion
        return {
            "success": True,
            "message": f"Activity {activity_index} deleted from day {day_index}"
        }
    except Exception as e:
        logger.error(f"Error deleting activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/refresh-activity")
async def refresh_activity(
    request: RefreshActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Refreshing activity for user {current_user.get('email')}")
        logger.debug(f"Request data: {request}")
        
        ai_provider = "openai"  # Default provider for now
        ai_client.set_provider(ai_provider) # Ensure client is set to the desired provider
        
        activity_type = request.activity.get('type', 'activity').lower()
        is_meal = activity_type == 'meal' or activity_type == 'food'
        
        try:
            # Call the new method in AIClient
            new_activity = await ai_client.refresh_activity_suggestion(
                original_activity=request.activity,
                custom_preferences=request.custom_preferences,
                activity_type=activity_type,
                is_meal=is_meal
            )
            
            logger.info(f"Successfully generated new activity via AIClient with {ai_provider} provider: {json.dumps(new_activity, indent=2)}")
            
            return {
                "success": True,
                "activity": new_activity
            }
            
        except ValueError as ve:
            logger.error(f"Error generating new activity via AIClient: {str(ve)}", exc_info=True)
            # Specific error for value errors from AIClient (e.g. no description)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh activity content: {str(ve)}"
            )
        except Exception as e:
            logger.error(f"Error refreshing activity with {ai_provider}: {str(e)}", exc_info=True)
            # General error from AIClient or other issues
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refresh activity: {str(e)}"
            )
            
    except HTTPException as he: # Catch HTTPExceptions raised above or by dependencies
        raise he
    except Exception as e: # Catch any other unexpected errors in the route handler itself
        logger.error(f"Error in refresh activity endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while refreshing the activity: {str(e)}"
        )
