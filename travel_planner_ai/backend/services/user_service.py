import logging
from datetime import datetime
from pymongo.collection import Collection
from fastapi import HTTPException, status
from ..models.user import User, UserCreate, UserResponse

logger = logging.getLogger(__name__)

def create_user_if_not_exists(users_collection: Collection, user_data: dict) -> User:
    """Create a new user if they don't exist, otherwise update their info."""
    logger.info(f"Checking if user exists: {user_data.get('email')}")
    logger.info(f"User data received: {user_data}")
    
    # Validate required fields
    required_fields = ['id', 'email', 'name']
    for field in required_fields:
        if not user_data.get(field):
            error_msg = f"Missing required field: {field}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
    
    # Try to find existing user by Google ID
    google_id = user_data["id"]
    existing_user = users_collection.find_one({"_id": google_id})
    
    if existing_user:
        logger.info(f"User already exists: {existing_user.get('email')}")
        # Update user data
        update_data = {
            "$set": {
                "email": user_data["email"],
                "name": user_data["name"],
                "updated_at": datetime.now()
            }
        }
        users_collection.update_one({"_id": google_id}, update_data)
        updated_user = users_collection.find_one({"_id": google_id})
        logger.info(f"Updated user data to: {updated_user.get('email')}, {updated_user.get('name')}")
        return User.model_validate(updated_user)
    
    logger.info(f"Creating new user with 10 free credits: {user_data['email']}")
    try:
        # Create new user document
        new_user_doc = {
            "_id": google_id,  # Use Google ID as MongoDB _id
            "email": user_data["email"],
            "name": user_data["name"],
            "available_credits": 10,  # Give 10 free credits
            "total_credits_purchased": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        users_collection.insert_one(new_user_doc)
        created_user = users_collection.find_one({"_id": google_id})
        if not created_user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        return User.model_validate(created_user)
        
    except Exception as e:
        error_msg = f"Error creating user: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

def get_user_by_id(users_collection: Collection, user_id: str) -> User:
    """
    Get a user by their ID.
    
    Args:
        users_collection: MongoDB users collection
        user_id: User ID
        
    Returns:
        User: The user if found
        
    Raises:
        HTTPException: If user not found
    """
    user = users_collection.find_one({"_id": user_id})
    
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User.model_validate(user) 