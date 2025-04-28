from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from fastapi import HTTPException
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the absolute path to the .env file
current_file = Path(__file__)
backend_dir = current_file.parent
env_path = backend_dir / '.env'

logger.debug(f"Looking for .env file at: {env_path}")
if not env_path.exists():
    raise FileNotFoundError(f".env file not found at {env_path}")

# Load environment variables
load_dotenv(dotenv_path=env_path)

MONGODB_URI = os.getenv("MONGODB_URI")
logger.debug("MONGODB_URI loaded: %s", MONGODB_URI[:20] + "..." if MONGODB_URI else None)

if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

try:
    # Safer logging that doesn't expose credentials
    logger.info("Attempting to connect to MongoDB...")
    client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
    
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")
    
    # Get database
    db = client.get_database("travel_planner")
    logger.info(f"Connected to database: {db.name}")
    
    # Get collections
    trips_collection = db.get_collection("trips")
    users_collection = db.get_collection("users")
    logger.info("Collections initialized")
    
except Exception as e:
    logger.error(f"Error connecting to MongoDB: {e}")
    raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def get_db():
    return db

def get_user_collection():
    return users_collection

def get_trips_collection():
    return trips_collection

# Example usage in your routes:
# async def get_user(user_id: str):
#     collection = await get_user_collection()
#     return await collection.find_one({"_id": user_id}) 