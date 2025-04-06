from fastapi import APIRouter, Depends, HTTPException, status, Body
from ..auth import get_current_user
from ..database import get_user_collection
from ..models.user import CreditsPurchase, CreditsPackage, UserResponse
from ..services.credits_service import (
    get_credits_packages, 
    get_user_credits, 
    add_credits, 
    create_payment_intent,
    verify_payment_intent
)
import logging
from typing import List, Dict, Any

# Set up logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["credits"])

@router.get("/credits/packages", response_model=List[CreditsPackage])
async def list_credits_packages():
    """Get available credits packages"""
    logger.info("Fetching available credits packages")
    return await get_credits_packages()

@router.get("/credits", response_model=Dict[str, int])
async def get_credits(
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    """Get current user's credits information"""
    logger.info(f"Fetching credits for user: {current_user['email']}")
    return await get_user_credits(users_collection, current_user["id"])

@router.post("/credits/payment-intent", response_model=Dict[str, Any])
async def create_stripe_payment_intent(
    purchase: CreditsPurchase,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe payment intent for purchasing credits"""
    logger.info(f"Creating payment intent for user {current_user['email']} - Package: {purchase.package_id}, Quantity: {purchase.quantity}")
    return await create_payment_intent(purchase.package_id, purchase.quantity)

@router.post("/credits/purchase", response_model=Dict[str, int])
async def purchase_credits(
    payment_intent_id: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
    users_collection = Depends(get_user_collection)
):
    """Process a credits purchase after payment is completed"""
    logger.info(f"Processing credits purchase for user {current_user['email']} with payment intent {payment_intent_id}")
    
    # Verify the payment intent
    payment_result = await verify_payment_intent(payment_intent_id)
    
    if not payment_result.get("verified"):
        logger.error(f"Payment verification failed for intent {payment_intent_id}: {payment_result}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed"
        )
    
    # Extract the credits amount from the payment metadata
    metadata = payment_result.get("metadata", {})
    credits_amount = int(metadata.get("credits", 0))
    
    if credits_amount <= 0:
        logger.error(f"Invalid credits amount in payment metadata: {metadata}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credits amount"
        )
    
    # Add the credits to the user's account
    logger.info(f"Adding {credits_amount} credits to user {current_user['id']}")
    return await add_credits(users_collection, current_user["id"], credits_amount)

@router.get("/credits/public-key", response_model=Dict[str, str])
async def get_stripe_public_key():
    """Get the Stripe publishable key"""
    from ..config import settings
    return {"publishable_key": settings.stripe_publishable_key} 