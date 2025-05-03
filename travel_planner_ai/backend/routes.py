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

@router.post("/trips")
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    users_collection = Depends(get_user_collection)
):
    try:
        # Check if we need to deduct credits
        user_id = current_user["id"]
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
        - User: {current_user['email']} (ID: {user_id})
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
        - User: {current_user['email']} (ID: {user_id})
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
    if user_id != current_user['id']:
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
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    try:
        logger.info(f"Generating itinerary for user {current_user['id']} ({current_user.get('email')})")
        
        # Log request data
        logger.info(f"Request data: {json.dumps(trip_request.formData, indent=2)}")
        
        # Deduct credits based on trip days
        user_id = current_user["id"]
        try:
            credits_result = deduct_credits_for_trip(users_collection, user_id, trip_request)
            logger.info(f"Credits deducted for itinerary generation. Remaining: {credits_result.get('available_credits', 'N/A')}")
        except HTTPException as credit_error:
            # Re-raise the exception to send appropriate error response to frontend
            raise credit_error

        # Generate itinerary using AI
        try:
            itinerary = await ai_client.generate_itinerary(trip_request.formData)
            
            # Log raw AI response
            logger.debug(f"Raw AI response: {json.dumps(itinerary, indent=2)}")
            
            if not itinerary or not isinstance(itinerary, dict):
                logger.error(f"Invalid AI response format: {itinerary}")
                raise ValueError("Invalid response from AI service")
            
            # Ensure the response has the correct structure
            if not itinerary.get('days'):
                logger.error("No days found in itinerary")
                raise ValueError("Invalid itinerary format: no days found")

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
                    if not activity.get('id'):
                        activity['id'] = f"{day['date']}-{id(activity)}"

            logger.info(f"Successfully formatted itinerary for {current_user.get('email')}")
            logger.debug(f"Final formatted itinerary: {json.dumps(itinerary, indent=2)}")
            
            # Add tripId and isOwner flag
            itinerary['tripId'] = f"temp-{datetime.now().timestamp()}"
            itinerary['isOwner'] = True
            
            return {
                "success": True,
                "itinerary": itinerary
            }
            
        except Exception as e:
            logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dear {current_user.get('email')}, we encountered an error: {str(e)}"
            )

    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dear {current_user.get('email')}, an unexpected error occurred"
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
        
        activity_type = request.activity.get('type', 'activity').lower()
        is_meal = activity_type == 'meal' or activity_type == 'food'
        
        # Generate a new activity using AI
        prompt = f"""
        Generate a new activity to replace:
        {request.activity.get('description')}
        
        IMPORTANT: Use this EXACT format:
        [ACTIVITY_START]
        Time: {request.activity.get('time')}
        Type: {activity_type}
        Description: (new activity description)
        Why: Explanation of why this activity is recommended
        Price: free|$|$$|$$$
        Location: Specific place name
        Coordinates: latitude,longitude (if available)
        [ACTIVITY_END]

        Rules:
        1. Keep the same time slot: {request.activity.get('time')}
        2. Keep similar type of activity and use the same responselanguage
        3. Make it family-friendly and engaging
        4. Include specific details and locations
        5. For the Location field, provide the exact name of the place (restaurant, museum, park, etc.)
        6. For the Coordinates field, provide the latitude and longitude if available, otherwise leave it blank
        """
        
        # Add specific instructions for meal activities
        if is_meal:
            prompt += """
        7. For meal activities, provide 2-3 specific restaurant options with brief descriptions
           Format the description like this: "Options include: 1. Restaurant Name - Brief description of cuisine and ambiance. 2. Restaurant Name - Brief description."
        """
        
        try:
            model_config = get_model_config(ai_client.model)
            response = await ai_client.client.chat.completions.create(
                model=ai_client.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel activity generator. Generate a single new activity using the exact format provided. It should be the same city as the original activity. For meal activities, always suggest 2-3 specific restaurant options with brief descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **model_config
            )
            
            content = response.choices[0].message.content
            logger.debug(f"AI response for refresh: {content}")
            
            # Parse the new activity
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            new_activity = {
                'id': request.activity.get('id'),
                'time': request.activity.get('time'),
                'type': activity_type
            }
            
            for line in lines:
                if line.startswith('Time: '):
                    new_activity['time'] = line.replace('Time: ', '').strip()
                elif line.startswith('Type: '):
                    new_activity['type'] = line.replace('Type: ', '').strip().lower()
                elif line.startswith('Description: '):
                    new_activity['description'] = line.replace('Description: ', '').strip()
                elif line.startswith('Location: '):
                    new_activity['location'] = line.replace('Location: ', '').strip()
                elif line.startswith('Coordinates: '):
                    coordinates = line.replace('Coordinates: ', '').strip()
                    if coordinates and coordinates != '(latitude,longitude if available)':
                        new_activity['coordinates'] = coordinates
            
            if not new_activity.get('description'):
                raise ValueError("No description generated for new activity")
            
            logger.info(f"Successfully generated new activity: {json.dumps(new_activity, indent=2)}")
            
            return {
                "success": True,
                "activity": new_activity
            }
            
        except Exception as e:
            logger.error(f"Error generating new activity: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
            
    except Exception as e:
        logger.error(f"Error refreshing activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
