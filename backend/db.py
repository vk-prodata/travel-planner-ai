# backend/db.py
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# Replace <username>, <password> and other parameters with your credentials.
MONGO_DETAILS = os.getenv("MONGO_DETAILS") or "mongodb+srv://<username>:<password>@cluster0.mongodb.net/travel_planner_db?retryWrites=true&w=majority"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.travel_planner_db
trips_collection = database.get_collection("trips")

async def save_trip(trip_data: dict) -> dict:
    result = await trips_collection.insert_one(trip_data)
    trip = await trips_collection.find_one({"_id": result.inserted_id})
    return trip

async def get_trip(trip_id: str) -> dict:
    trip = await trips_collection.find_one({"trip_id": trip_id})
    return trip
