#!/usr/bin/env python
"""
Script to update a user's temporary email and name with their real Google Auth data.
Run this script with: 
    poetry run python -m travel_planner_ai.backend.scripts.update_user [user_id] [email] [name]
"""

import sys
import logging
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check arguments
    if len(sys.argv) < 4:
        logger.error("Usage: python update_user.py [user_id] [email] [name]")
        sys.exit(1)
    
    user_id = sys.argv[1]
    email = sys.argv[2]
    name = " ".join(sys.argv[3:])  # Allow spaces in name
    
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        logger.error("MONGODB_URI environment variable not set")
        sys.exit(1)
    
    logger.info(f"Connecting to MongoDB...")
    client = MongoClient(mongodb_uri)
    db = client.get_database("travel_planner")
    users_collection = db.get_collection("users")
    
    # Find the user
    logger.info(f"Looking up user with ID: {user_id}")
    user = users_collection.find_one({"_id": user_id})
    
    if not user:
        logger.error(f"User with ID {user_id} not found")
        sys.exit(1)
    
    # Display current user data
    logger.info(f"Current user data:")
    logger.info(f"  Email: {user.get('email')}")
    logger.info(f"  Name: {user.get('name')}")
    logger.info(f"  Available Credits: {user.get('available_credits')}")
    logger.info(f"  Total Credits Purchased: {user.get('total_credits_purchased')}")
    
    # Update the user
    logger.info(f"Updating user data to:")
    logger.info(f"  Email: {email}")
    logger.info(f"  Name: {name}")
    
    result = users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "email": email,
                "name": name,
                "updated_at": datetime.now()
            }
        }
    )
    
    if result.modified_count == 0:
        logger.warning("No changes made to the user data")
    else:
        logger.info(f"Successfully updated user data")
    
    # Display updated user data
    updated_user = users_collection.find_one({"_id": user_id})
    logger.info(f"Updated user data:")
    logger.info(f"  Email: {updated_user.get('email')}")
    logger.info(f"  Name: {updated_user.get('name')}")
    logger.info(f"  Available Credits: {updated_user.get('available_credits')}")
    logger.info(f"  Total Credits Purchased: {updated_user.get('total_credits_purchased')}")

if __name__ == "__main__":
    main() 