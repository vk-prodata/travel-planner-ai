from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from fastapi import HTTPException
import os
from dotenv import load_dotenv
import logging

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info(f"Attempting to connect to MongoDB with URI: {MONGODB_URI.split('@')[0]}/*****@{MONGODB_URI.split('@')[1]}")
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

# Simplified collection access
def get_trips_collection():
    return trips_collection

# Async functions for collection access
async def get_user_collection():
    return users_collection

# Example usage in your routes:
# async def get_user(user_id: str):
#     collection = await get_user_collection()
#     return await collection.find_one({"_id": user_id}) 