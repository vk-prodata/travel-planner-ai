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
        credits=30,
        price=4.99,
        is_popular=False
    ),
    CreditsPackage(
        id="premium",
        name="Premium Package",
        credits=300,
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
    logger.debug(f"Attempting to fetch credits for user_id: {user_id}")
    user = users_collection.find_one({"_id": user_id})
    
    if not user:
        logger.info(f"User {user_id} not found in DB while fetching credits.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    credits_info = {
        "available_credits": user.get("available_credits", 0),
        "total_credits_purchased": user.get("total_credits_purchased", 0),
        "availableCredits": user.get("available_credits", 0),
        "totalCreditsPurchased": user.get("total_credits_purchased", 0)
    }
    logger.info(f"Successfully fetched credits for user_id {user_id}: {credits_info}")
    return credits_info


def add_credits(users_collection: Collection, user_id: str, credits_amount: int) -> Dict[str, Any]:
    """Add credits to a user's account"""
    logger.info(f"Attempting to add {credits_amount} credits to user {user_id}")
    
    # Get the current user
    user = users_collection.find_one({"_id": user_id})
    if not user:
        logger.error(f"User with ID {user_id} not found when trying to add credits.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update the credits
    current_credits = user.get("available_credits", 0)
    total_purchased = user.get("total_credits_purchased", 0)
    new_available = current_credits + credits_amount
    new_total_purchased = total_purchased + credits_amount
    
    logger.debug(f"User {user_id} current credits: {current_credits}, total purchased: {total_purchased}. Adding {credits_amount}.")
    
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "available_credits": new_available,
                "total_credits_purchased": new_total_purchased,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        logger.error(f"MongoDB update operation modified 0 documents for user {user_id} when adding credits.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user credits in database"
        )
    
    # Get the updated user to confirm and return new values
    updated_user = users_collection.find_one({"_id": user_id})
    if not updated_user:
         logger.error(f"User {user_id} disappeared after successful credit update?!")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user after updating credits"
         )

    updated_credits_info = {
        "available_credits": updated_user.get("available_credits", 0),
        "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
        "availableCredits": updated_user.get("available_credits", 0),
        "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
    }
    logger.info(f"Successfully added {credits_amount} credits to user {user_id}. New info: {updated_credits_info}")
    return updated_credits_info


def deduct_credits(users_collection: Collection, user_id: str, credits_amount: int = 1) -> Dict[str, Any]:
    """Deduct credits from a user's account"""
    logger.info(f"Attempting to deduct {credits_amount} credits from user {user_id}")
    
    # Get the current user
    user = users_collection.find_one({"_id": user_id})
    if not user:
        logger.error(f"User with ID {user_id} not found when trying to deduct credits.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the user has enough credits
    current_credits = user.get("available_credits", 0)
    logger.debug(f"User {user_id} current credits: {current_credits}. Required: {credits_amount}." )
    if current_credits < credits_amount:
        logger.warning(f"User {user_id} insufficient credits. Has: {current_credits}, Required: {credits_amount}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. You need {credits_amount} credits but have {current_credits}."
        )
    
    # Deduct the credits
    new_available = current_credits - credits_amount
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "available_credits": new_available,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        logger.error(f"MongoDB update operation modified 0 documents for user {user_id} when deducting credits.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user credits in database"
        )
    
    # Get the updated user
    updated_user = users_collection.find_one({"_id": user_id})
    if not updated_user:
         logger.error(f"User {user_id} disappeared after successful credit deduction?!")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user after deducting credits"
         )

    updated_credits_info = {
        "available_credits": updated_user.get("available_credits", 0),
        "total_credits_purchased": updated_user.get("total_credits_purchased", 0),
        "availableCredits": updated_user.get("available_credits", 0),
        "totalCreditsPurchased": updated_user.get("total_credits_purchased", 0)
    }
    logger.info(f"Successfully deducted {credits_amount} credits from user {user_id}. New info: {updated_credits_info}")
    return updated_credits_info


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


def deduct_credits_for_trip(users_collection: Collection, user_id: str, trip_data) -> Dict[str, Any]:
    """
    Deduct credits based on trip duration (number of days).
    This consolidates the credit deduction logic used across multiple routers.
    
    Args:
        users_collection: MongoDB collection for users
        user_id: User ID to deduct credits from
        trip_data: Trip data containing either itinerary.days or formData with date range
        
    Returns:
        Dict with updated credit information
        
    Raises:
        HTTPException: If user not found or has insufficient credits
    """
    logger.info(f"Calculating credit deduction for trip by user {user_id}")
    
    # Calculate credits to deduct based on days count
    days_count = 0
    
    # Try to get days from itinerary if it exists
    if hasattr(trip_data, 'itinerary') and trip_data.itinerary:
        itinerary = trip_data.itinerary
        if isinstance(itinerary, dict) and "days" in itinerary:
            days_count = len(itinerary["days"])
    
    # If no days are in the itinerary yet, try to calculate from form data
    if days_count == 0 and hasattr(trip_data, 'formData') and trip_data.formData:
        form_data = trip_data.formData
        if "startDate" in form_data and "endDate" in form_data:
            try:
                from datetime import datetime
                start_date = datetime.fromisoformat(form_data["startDate"].replace("Z", "+00:00"))
                end_date = datetime.fromisoformat(form_data["endDate"].replace("Z", "+00:00"))
                
                # Calculate inclusive days without adding extra day
                # For example: Jan 1 to Jan 7 is 7 days, not 8
                delta = end_date - start_date
                days_count = delta.days
                
                # Only add 1 if start_date and end_date are the same day
                if days_count == 0:
                    days_count = 1
                    
                logger.info(f"Calculated {days_count} days for trip from {start_date.date()} to {end_date.date()}")
            except Exception as e:
                logger.error(f"Error calculating trip duration from dates: {str(e)}")
                days_count = 1  # Default to 1 day if calculation fails
        elif "tripDuration" in form_data:
            try:
                days_count = int(form_data["tripDuration"])
            except (ValueError, TypeError):
                days_count = 1
    
    # Ensure minimum of 1 day for credit purposes
    days_count = max(1, days_count)
    
    try:
        logger.info(f"Deducting {days_count} credits for {days_count}-day trip from user {user_id}")
        return deduct_credits(users_collection, user_id, days_count)
    except HTTPException as credit_error:
        # Re-raise the HTTPException
        logger.warning(f"Credit deduction failed for user {user_id}: {credit_error.detail}")
        raise credit_error
    except Exception as e:
        # Log and wrap any other exceptions
        logger.error(f"Unexpected error during credit deduction for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing credits."
        ) 