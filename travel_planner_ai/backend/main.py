# backend/main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from travel_planner_ai.backend.routes import router as trip_router
from travel_planner_ai.backend.routers.trips import router as trips_router
from travel_planner_ai.backend.routers.credits import router as credits_router
from travel_planner_ai.backend.routers.contact import router as contact_router
from .config.logging_config import setup_logging
from .auth import get_current_user
from .database import get_user_collection
import logging
import time
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import status
from datetime import datetime
from fastapi.responses import JSONResponse
from .models.user import User, UserResponse
from .services.jwt_service import jwt_service

# Setup logging
app_logger = setup_logging()
logger = logging.getLogger("travel_planner_ai.main")
logger.info("Starting Travel Planner AI application")

# Load environment variables
load_dotenv(dotenv_path="travel_planner_ai/.env")

app = FastAPI(title="Travel Planner AI")

# Configure CORS for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3002",
        "https://www.travelplannerai.org",
        "https://travelplannerai.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers without prefixes to match frontend expectations
app.include_router(trip_router)    # No prefix for routes to match frontend calls
app.include_router(trips_router)   # No prefix since it already includes "/trips" in routes
app.include_router(credits_router) # Include the new credits router
app.include_router(contact_router) # Include the contact router

logger.info("Routers configured and ready")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get request details
    method = request.method
    url = str(request.url)
    client_host = request.client.host if request.client else "unknown"
    
    # Generate a request ID
    request_id = f"{int(time.time())}-{hash(url) % 10000:04d}"
    
    # Log request
    logger.info(f"[{request_id}] Request started: {method} {url} from {client_host}")
    
    # Try to log request body for POST/PUT requests
    if method in ["POST", "PUT"]:
        try:
            body = await request.body()
            if body:
                # Only log the first 1000 characters to avoid huge logs
                body_str = body.decode('utf-8')[:1000]
                if len(body_str) == 1000:
                    body_str += "... [truncated]"
                logger.debug(f"[{request_id}] Request body: {body_str}")
        except Exception as e:
            logger.warning(f"[{request_id}] Could not log request body: {str(e)}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"[{request_id}] Request completed: {method} {url} - Status: {response.status_code} - Time: {process_time:.4f}s")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Request failed: {method} {url} - Error: {str(e)} - Time: {process_time:.4f}s")
        raise

# Add cookie middleware
@app.middleware("http")
async def add_secure_cookie_settings(request, call_next):
    response = await call_next(request)
    if response.headers.get("set-cookie"):
        response.headers["set-cookie"] += "; SameSite=Strict; Secure"
    return response

@app.get("/test")
async def test():
    logger.info("Test endpoint accessed")
    return {
        "status": "ok",
        "message": "Backend is working",
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Travel Planner AI API"}

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")  # Changed from MONGO_URI to MONGODB_URI to match your environment
if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

client = MongoClient(MONGO_URI)
db = client.travel_planner
users_collection = db.users

# Google OAuth setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")

@app.post("/auth/google/callback")
async def google_auth_callback(
    request: Request,
    users_collection = Depends(get_user_collection)
):
    """
    Handle OAuth callback for embedded browsers (like Telegram)
    Exchange authorization code for access token
    """
    try:
        body = await request.json()
        code = body.get('code')
        redirect_uri = body.get('redirect_uri')
        state = body.get('state')
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        logger.info(f"Processing OAuth callback with code: {code[:10]}...")
        
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': os.getenv("GOOGLE_CLIENT_SECRET"),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri or f"{request.base_url}auth/callback"
        }
        
        import requests
        token_response = requests.post(token_url, data=token_data)
        
        if not token_response.ok:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for token"
            )
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google"
            )
        
        # Now use this access token to get user info (same as existing flow)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=access_token
        )
        
        user_data = await get_current_user(credentials, users_collection)
        
        # Convert to dict if it's a Pydantic model
        if hasattr(user_data, 'model_dump'):
            user_data = user_data.model_dump()
        elif hasattr(user_data, 'dict'):
            user_data = user_data.dict()
        
        # Generate JWT tokens for longer sessions
        user_id = user_data.get("id") or user_data.get("_id")
        jwt_access_token = jwt_service.create_access_token(user_data)
        jwt_refresh_token = jwt_service.create_refresh_token(user_id)
        
        # Store refresh tokens
        update_data = {"updated_at": datetime.now()}
        if refresh_token:
            update_data["google_refresh_token"] = refresh_token
        update_data["jwt_refresh_token"] = jwt_refresh_token
        
        users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        logger.info(f"OAuth callback successful for user: {user_data['email']}")
        
        # Return user response with JWT tokens
        response = UserResponse(
            id=user_id,
            email=user_data["email"],
            name=user_data["name"],
            available_credits=user_data.get("available_credits", 0),
            total_credits_purchased=user_data.get("total_credits_purchased", 0)
        )
        
        # Add JWT tokens to response headers
        headers = {
            "X-Access-Token": jwt_access_token,
            "X-Refresh-Token": jwt_refresh_token
        }
        
        return JSONResponse(
            content=response.model_dump(),
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error in google_auth_callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/auth/google", response_model=UserResponse)
async def google_auth(
    request: Request,
    users_collection = Depends(get_user_collection)
):
    """
    Authenticate user with Google OAuth token and return user data with JWT token
    """
    try:
        # Get token from request body
        body = await request.json()
        token = body.get('token')
        refresh_token = body.get('refresh_token')
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required"
            )
        
        # Create credentials object for get_current_user
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Get user data using existing auth flow
        user_data = await get_current_user(credentials, users_collection)
        
        # Convert to dict if it's a Pydantic model
        if hasattr(user_data, 'model_dump'):
            user_data = user_data.model_dump()
        elif hasattr(user_data, 'dict'):
            user_data = user_data.dict()
        
        # Generate JWT tokens for longer sessions
        user_id = user_data.get("id") or user_data.get("_id")
        jwt_access_token = jwt_service.create_access_token(user_data)
        jwt_refresh_token = jwt_service.create_refresh_token(user_id)
        
        # Store refresh tokens if provided
        update_data = {"updated_at": datetime.now()}
        if refresh_token:
            update_data["google_refresh_token"] = refresh_token
        update_data["jwt_refresh_token"] = jwt_refresh_token
        
        users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
            
        logger.info(f"User data before response: {user_data}")
        
        # Return user response with JWT tokens
        response = UserResponse(
            id=user_id,
            email=user_data["email"],
            name=user_data["name"],
            available_credits=user_data.get("available_credits", 0),
            total_credits_purchased=user_data.get("total_credits_purchased", 0)
        )
        
        # Add JWT tokens to response headers
        headers = {
            "X-Access-Token": jwt_access_token,
            "X-Refresh-Token": jwt_refresh_token
        }
        
        return JSONResponse(
            content=response.model_dump(),
            headers=headers
        )
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except Exception as e:
        logger.error(f"Error in google_auth: {str(e)}")
        logger.error(f"User data at error: {user_data if 'user_data' in locals() else 'Not available'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/auth/refresh")
async def refresh_token(
    request: Request,
    users_collection = Depends(get_user_collection)
):
    """
    Refresh JWT access token using refresh token
    """
    try:
        body = await request.json()
        refresh_token = body.get('refresh_token')
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Generate new access token
        new_access_token = jwt_service.refresh_access_token(refresh_token, users_collection)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Run with: uvicorn main:app --reload
