import logging
from datetime import datetime
from pymongo.collection import Collection
from fastapi import HTTPException, status
from ..models.user import User, UserCreate, UserResponse

logger = logging.getLogger(__name__)

async def create_user_if_not_exists(users_collection: Collection, user_data: dict) -> User:
    """
    Create a user if they don't already exist in the database.
    Grants 1 free credit on signup.
    
    Args:
        users_collection: MongoDB users collection
        user_data: Dictionary with user information (id, email, name)
        
    Returns:
        User: The created or existing user
    """
    logger.info(f"Checking if user exists: {user_data.get('email')}")
    
    # Check if user exists
    existing_user = await users_collection.find_one({"id": user_data["id"]})
    
    if existing_user:
        logger.info(f"User already exists: {user_data.get('email')}")
        return User(**existing_user)
    
    # Create new user with 1 free credit
    logger.info(f"Creating new user with 1 free credit: {user_data.get('email')}")
    
    user_create = UserCreate(**user_data)
    
    now = datetime.now()
    new_user = User(
        id=user_create.id,
        email=user_create.email,
        name=user_create.name,
        available_credits=1,  # Grant 1 free credit on signup
        total_credits_purchased=0,
        created_at=now,
        updated_at=now
    )
    
    # Insert into database
    try:
        await users_collection.insert_one(new_user.dict())
        logger.info(f"Successfully created user: {new_user.email}")
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

async def get_user_by_id(users_collection: Collection, user_id: str) -> User:
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
    user = await users_collection.find_one({"id": user_id})
    
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(**user) 