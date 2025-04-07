import logging
import stripe
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from datetime import datetime
from ..config import settings
from ..models.user import CreditsPackage

# Configure logging
logger = logging.getLogger(__name__)

# Configure Stripe
logger.info(f"Setting Stripe API key from settings")
stripe.api_key = settings.stripe_secret_key

# Define credit packages
CREDITS_PACKAGES = [
    CreditsPackage(
        id="basic",
        name="Basic Package",
        credits=10,
        price=4.99,
        is_popular=False
    ),
    CreditsPackage(
        id="value",
        name="Value Package",
        credits=100,
        price=39.99,
        is_popular=True
    )
]

def get_credits_packages() -> List[CreditsPackage]:
    """Get the available credits packages"""
    return CREDITS_PACKAGES


def get_package_by_id(package_id: str) -> Optional[CreditsPackage]:
    """Get a specific credits package by its ID"""
    for package in CREDITS_PACKAGES:
        if package.id == package_id:
            return package
    return None


def get_user_credits(users_collection: Collection, user_id: str) -> Dict[str, Any]:
    """Get the credits information for a user"""
    user = users_collection.find_one({"_id": user_id})
    
    if not user:
        logger.error(f"User with ID {user_id} not found")
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


def add_credits(users_collection: Collection, user_id: str, credits_amount: int) -> Dict[str, Any]:
    """Add credits to a user's account"""
    logger.info(f"Adding {credits_amount} credits to user {user_id}")
    
    # Get the current user
    user = users_collection.find_one({"_id": user_id})
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update the credits
    current_credits = user.get("available_credits", 0)
    total_purchased = user.get("total_credits_purchased", 0)
    
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "available_credits": current_credits + credits_amount,
                "total_credits_purchased": total_purchased + credits_amount,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        logger.error(f"Failed to update credits for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user credits"
        )
    
    # Get the updated user
    updated_user = users_collection.find_one({"_id": user_id})
    
    # Return with both naming conventions to support frontend
    return {
        "available_credits": updated_user.get("available_credits", 0),
        "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
        "availableCredits": updated_user.get("available_credits", 0),
        "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
    }


def deduct_credits(users_collection: Collection, user_id: str, credits_amount: int = 1) -> Dict[str, Any]:
    """Deduct credits from a user's account"""
    logger.info(f"Deducting {credits_amount} credits from user {user_id}")
    
    # Get the current user
    user = users_collection.find_one({"_id": user_id})
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the user has enough credits
    current_credits = user.get("available_credits", 0)
    if current_credits < credits_amount:
        logger.error(f"User {user_id} does not have enough credits. Has: {current_credits}, Required: {credits_amount}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. You need {credits_amount} credits but have {current_credits}."
        )
    
    # Deduct the credits
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "available_credits": current_credits - credits_amount,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        logger.error(f"Failed to deduct credits for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user credits"
        )
    
    # Get the updated user
    updated_user = users_collection.find_one({"_id": user_id})
    
    # Return with both naming conventions to support frontend
    return {
        "available_credits": updated_user.get("available_credits", 0),
        "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
        "availableCredits": updated_user.get("available_credits", 0),
        "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
    }


def create_payment_intent(package_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Create a Stripe payment intent for credits purchase"""
    package = get_package_by_id(package_id)
    if not package:
        logger.error(f"Credits package with ID {package_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credits package not found"
        )
    
    amount_in_cents = int(package.price * 100) * quantity
    
    try:
        logger.info(f"Creating payment intent for {quantity} x {package.name} (${package.price * quantity})")
        
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            description=f"Purchase of {quantity} x {package.name} ({package.credits * quantity} credits)",
            metadata={
                "package_id": package.id,
                "credits": package.credits * quantity,
                "quantity": quantity
            }
        )
        
        return {
            "client_secret": payment_intent.client_secret,
            "package": package.model_dump(),
            "quantity": quantity,
            "total_credits": package.credits * quantity,
            "total_amount": package.price * quantity
        }
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment: {str(e)}"
        )


def verify_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """Verify a Stripe payment intent for credits purchase"""
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != "succeeded":
            logger.error(f"Payment intent {payment_intent_id} has status {payment_intent.status}, not succeeded")
            return {
                "verified": False,
                "status": payment_intent.status
            }
        
        # Payment succeeded
        return {
            "verified": True,
            "status": payment_intent.status,
            "metadata": payment_intent.metadata
        }
    except Exception as e:
        logger.error(f"Error verifying payment intent {payment_intent_id}: {str(e)}")
        return {
            "verified": False,
            "error": str(e)
        } 