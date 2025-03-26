# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from travel_planner_ai.backend.routes import router as trip_router
from travel_planner_ai.backend.routers.trips import router as trips_router
from .config.logging_config import setup_logging
import logging
import time
import json

# Setup logging
app_logger = setup_logging()
logger = logging.getLogger("travel_planner_ai.main")
logger.info("Starting Travel Planner AI application")

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
app.include_router(trip_router)  # No prefix for routes to match frontend calls
app.include_router(trips_router)  # No prefix since it already includes "/trips" in routes

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

# Run with: uvicorn main:app --reload
