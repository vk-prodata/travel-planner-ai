from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from .config import settings  # Use relative import
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            try:
                cls.client = AsyncIOMotorClient(settings.mongodb_url)
                # Test the connection
                cls.client.admin.command('ping')
                logger.info("Successfully connected to MongoDB Atlas")
            except Exception as e:
                logger.error(f"Error connecting to MongoDB Atlas: {e}")
                raise
        return cls.client
    
    @classmethod
    def get_db(cls):
        return cls.get_client().get_database('travel_planner')

    @classmethod
    def get_trips_collection(cls):
        return cls.get_db()['trip']  # Use 'trip' collection

# Simplified collection access
def get_trips_collection():
    return Database.get_trips_collection()

# Async functions for collection access
async def get_user_collection():
    return Database.get_db().users

# Example usage in your routes:
# async def get_user(user_id: str):
#     collection = await get_user_collection()
#     return await collection.find_one({"_id": user_id}) 