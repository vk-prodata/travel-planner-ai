from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from .config import settings

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
        return cls.client
    
    @classmethod
    def get_db(cls):
        return cls.get_client().get_database('travel_planner')

# Async functions for collection access
async def get_user_collection():
    return Database.get_db().users

async def get_trips_collection():
    return Database.get_db().trips

# Example usage in your routes:
# async def get_user(user_id: str):
#     collection = await get_user_collection()
#     return await collection.find_one({"_id": user_id}) 