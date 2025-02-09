# backend/db.py
from motor import motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_DETAILS = os.getenv("MONGODB_URL")
if not MONGO_DETAILS:
    raise ValueError("MONGODB_URL environment variable is not set")

client = motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.travel_planner
trip_collection = database.get_collection("trips")

async def save_trip(trip_data: dict) -> dict:
    result = await trip_collection.insert_one(trip_data)
    trip = await trip_collection.find_one({"_id": result.inserted_id})
    return trip

async def get_trip(trip_id: str) -> dict:
    trip = await trip_collection.find_one({"trip_id": trip_id})
    return trip
