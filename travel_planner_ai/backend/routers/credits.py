from fastapi import APIRouter, Depends, HTTPException, status, Body
from ..auth import get_current_user
from ..database import get_user_collection
from ..models.user import CreditsPurchase, CreditsPackage, UserResponse
from ..services.credits_service import (
    get_credits_packages, 
    get_user_credits, 
    add_credits, 
    create_payment_intent,
    verify_payment_intent,
    get_package_by_id
)
from ..services.user_service import create_user_if_not_exists
import logging
from typing import List, Dict, Any
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["credits"])

@router.get("/credits/packages", response_model=List[CreditsPackage])
async def list_credits_packages():
    """Get available credits packages"""
    logger.info("Fetching available credits packages")
    return get_credits_packages()

@router.get("/credits", response_model=Dict[str, int])
async def get_credits(
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    """Get current user's credits information"""
    logger.info(f"Fetching credits for user: {current_user['email']}")
    
    try:
        # Check if user exists
        user = users_collection.find_one({"id": current_user["id"]})
        
        if not user:
            logger.error(f"User with ID {current_user['id']} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return with both naming conventions to support frontend
        return {
            "available_credits": user.get("available_credits", 0),
            "total_credits_purchased": user.get("total_credits_purchased", 0),
            "availableCredits": user.get("available_credits", 0),
            "totalCreditsPurchased": user.get("total_credits_purchased", 0)
        }
    except Exception as e:
        logger.error(f"Error getting credits for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching credits: {str(e)}"
        )

@router.get("/credits/{user_id}", response_model=Dict[str, int])
async def get_user_credits_by_id(
    user_id: str,
    users_collection = Depends(get_user_collection)
):
    """Get a user's credits information by user ID"""
    logger.info(f"Fetching credits for user ID: {user_id}")
    try:
        # Check if user exists
        user = await users_collection.find_one({"_id": user_id})
        
        if not user:
            logger.info(f"User {user_id} not found, will be created during Google auth")
            # Return default credits for new user
            return {
                "available_credits": 1,  # Default free credit
                "total_credits_purchased": 0,
                "availableCredits": 1,
                "totalCreditsPurchased": 0
            }
        
        # Return the user's credits with both naming conventions
        return {
            "available_credits": user.get("available_credits", 1),
            "total_credits_purchased": user.get("total_credits_purchased", 0),
            "availableCredits": user.get("available_credits", 1),
            "totalCreditsPurchased": user.get("total_credits_purchased", 0)
        }
            
    except Exception as e:
        logger.error(f"Error getting user credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user credits: {str(e)}"
        )

@router.post("/credits/payment-intent", response_model=Dict[str, Any])
async def create_stripe_payment_intent(
    purchase: CreditsPurchase,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe payment intent for purchasing credits"""
    logger.info(f"Creating payment intent for user {current_user['email']} - Package: {purchase.package_id}, Quantity: {purchase.quantity}")
    return create_payment_intent(purchase.package_id, purchase.quantity)

@router.post("/credits/purchase", response_model=Dict[str, int])
async def purchase_credits(
    userId: str = Body(...),
    packageId: str = Body(...),
    users_collection = Depends(get_user_collection)
):
    """Process a direct credits purchase (for testing only)"""
    logger.info(f"Processing direct credits purchase for user {userId} with package {packageId}")
    
    # Get the package to determine credit amount
    package = get_package_by_id(packageId)
    if not package:
        logger.error(f"Credits package with ID {packageId} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credits package not found"
        )
    
    credits_amount = package.credits
    logger.info(f"Adding {credits_amount} credits to user {userId}")
    
    try:
        # Check if user exists
        user = users_collection.find_one({"_id": userId})
        if not user:
            logger.error(f"User {userId} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please log in with Google first."
            )
            
        # Update the credits
        current_credits = user.get("available_credits", 0)
        total_purchased = user.get("total_credits_purchased", 0)
        
        users_collection.update_one(
            {"_id": userId},
            {
                "$set": {
                    "available_credits": current_credits + credits_amount,
                    "total_credits_purchased": total_purchased + credits_amount,
                    "updated_at": datetime.now()
                }
            }
        )
        
        logger.info(f"Updated user {userId} credits: +{credits_amount}")
        
        # Get updated user
        updated_user = users_collection.find_one({"_id": userId})
        
        return {
            "available_credits": updated_user.get("available_credits", 0),
            "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
            "availableCredits": updated_user.get("available_credits", 0),
            "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
        }
            
    except Exception as e:
        logger.error(f"Error adding credits to user {userId}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding credits: {str(e)}"
        )

@router.post("/credits/purchase-with-payment", response_model=Dict[str, int])
async def purchase_credits_with_payment(
    payment_intent_id: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    """Process a credits purchase after payment is completed"""
    logger.info(f"Processing credits purchase with payment intent: {payment_intent_id}")
    
    try:
        # Verify the payment intent
        payment_intent = verify_payment_intent(payment_intent_id)
        if not payment_intent:
            logger.error(f"Invalid payment intent: {payment_intent_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment intent"
            )
            
        # Get the credits package
        package_id = payment_intent.metadata.get("package_id")
        if not package_id:
            logger.error(f"No package ID in payment intent metadata")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No package ID found"
            )
            
        package = get_package_by_id(package_id)
        if not package:
            logger.error(f"Invalid package ID: {package_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid package ID"
            )
            
        credits_amount = package.credits
        logger.info(f"Credits amount from package: {credits_amount}")
    
        # Create or get user with create_user_if_not_exists
        user = await create_user_if_not_exists(users_collection, current_user)
        if not isinstance(user, dict):
            user = user.dict()
            
        # Update the credits
        current_credits = user.get("available_credits", 0)
        total_purchased = user.get("total_credits_purchased", 0)
        
        await users_collection.update_one(
            {"_id": current_user["id"]},
            {
                "$set": {
                    "available_credits": current_credits + credits_amount,
                    "total_credits_purchased": total_purchased + credits_amount,
                    "updated_at": datetime.now()
                }
            }
        )
        
        logger.info(f"Updated user {current_user['id']} credits: +{credits_amount}")
        
        # Get updated user
        updated_user = await users_collection.find_one({"_id": current_user["id"]})
        
        return {
            "available_credits": updated_user.get("available_credits", 0),
            "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
            "availableCredits": updated_user.get("available_credits", 0),
            "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
        }
    except Exception as e:
        logger.error(f"Error adding credits to user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding credits: {str(e)}"
        )

@router.get("/credits/public-key", response_model=Dict[str, str])
async def get_stripe_public_key():
    """Get the Stripe publishable key"""
    from ..config import settings
    return {"publishable_key": settings.stripe_publishable_key}

@router.post("/credits/update-user", response_model=Dict[str, Any])
async def update_user_data(
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    """Update temporary user data with real Google Auth information"""
    user_id = current_user["id"]
    logger.info(f"Manually updating user data for user ID: {user_id}")
    
    try:
        # Check if user exists
        user = users_collection.find_one({"_id": user_id})
        
        if not user:
            logger.error(f"User with ID {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update the user with current Google Auth information
        result = users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "email": current_user["email"],
                    "name": current_user.get("name", ""),
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count == 0 and user.get("email") == current_user["email"] and user.get("name") == current_user.get("name", ""):
            # No changes needed - already up to date
            return {
                "success": True,
                "message": "User data already up to date",
                "user": {
                    "id": user_id,
                    "email": user.get("email"),
                    "name": user.get("name"),
                    "available_credits": user.get("available_credits", 0),
                    "total_credits_purchased": user.get("total_credits_purchased", 0)
                }
            }
        
        if result.modified_count == 0:
            logger.error(f"Failed to update user data for {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user data"
            )
        
        # Get updated user
        updated_user = users_collection.find_one({"_id": user_id})
        
        return {
            "success": True,
            "message": "User data updated successfully",
            "user": {
                "id": user_id,
                "email": updated_user.get("email"),
                "name": updated_user.get("name"),
                "available_credits": updated_user.get("available_credits", 0),
                "total_credits_purchased": updated_user.get("total_credits_purchased", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error updating user data for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user data: {str(e)}"
        ) 