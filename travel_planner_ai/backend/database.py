from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the path to the .env file in the project root
current_file = Path(__file__)
backend_dir = current_file.parent
project_root = backend_dir.parent  # Go one level up to the project root
env_path = project_root / '.env'

logger.debug(f"Attempting to load .env file from: {env_path}")
# Load environment variables from .env if it exists (useful for local dev)
# In production (like Render), variables should be set directly in the environment.
# override=False ensures that system environment variables take precedence.
load_dotenv(dotenv_path=env_path, override=False)

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
# Get database name from environment, default to "travel_planner" if not specified
DB_NAME = os.getenv("DB_NAME", "travel_planner")
# Connection pool settings
MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
MAX_IDLE_TIME_MS = int(os.getenv("MONGO_MAX_IDLE_TIME_MS", "60000"))  # 1 minute
CONNECTION_TIMEOUT_MS = int(os.getenv("MONGO_CONNECTION_TIMEOUT_MS", "30000"))  # 30 seconds

# Safely log configuration without exposing credentials
if MONGODB_URI:
    # Extract host from URI for logging (don't log credentials)
    try:
        uri_parts = MONGODB_URI.split('@')
        if len(uri_parts) > 1:
            host_info = uri_parts[1].split('/')[0]
            logger.info(f"MongoDB configured to connect to: {host_info}")
        else:
            logger.info("MongoDB URI loaded (format not recognized for safe logging)")
    except Exception:
        logger.info("MongoDB URI loaded (unable to parse for safe logging)")
else:
    logger.critical("MONGODB_URI environment variable is not set or loaded")
    raise ValueError("MONGODB_URI environment variable is not set or loaded")

# Connection retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2

# Initialize global references
client = None
db = None
trips_collection = None
users_collection = None

def initialize_db_connection():
    """Initialize database connection with retry logic"""
    global client, db, trips_collection, users_collection
    
    retry_count = 0
    last_error = None
    
    while retry_count < MAX_RETRY_ATTEMPTS:
        try:
            logger.info(f"Attempting to connect to MongoDB (attempt {retry_count + 1}/{MAX_RETRY_ATTEMPTS})...")
            
            # Initialize MongoDB client with optimized settings
            client = MongoClient(
                MONGODB_URI, 
                server_api=ServerApi('1'),
                maxPoolSize=MAX_POOL_SIZE,
                minPoolSize=MIN_POOL_SIZE,
                maxIdleTimeMS=MAX_IDLE_TIME_MS,
                connectTimeoutMS=CONNECTION_TIMEOUT_MS,
                retryWrites=True,
                w='majority'  # Write concern for better data durability
            )
            
            # Verify connection with a ping
            client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
            # Get database
            db = client.get_database(DB_NAME)
            logger.info(f"Connected to database: {DB_NAME}")
            
            # Get collections
            trips_collection = db.get_collection("trips")
            users_collection = db.get_collection("users")
            logger.info("Collections initialized")
            
            # Successfully connected and initialized
            return
            
        except ConnectionFailure as e:
            last_error = e
            logger.warning(f"MongoDB connection failure (attempt {retry_count + 1}): {e}")
        except ServerSelectionTimeoutError as e:
            last_error = e
            logger.warning(f"MongoDB server selection timeout (attempt {retry_count + 1}): {e}")
        except OperationFailure as e:
            last_error = e
            logger.error(f"MongoDB operation failure: {e}")
            # Operation failures are usually due to auth issues or command failures
            # Don't retry these as they're unlikely to resolve with just retries
            break
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            # For unexpected errors, attempt retry too
        
        # Increment retry counter
        retry_count += 1
        
        # If we're going to retry, sleep first
        if retry_count < MAX_RETRY_ATTEMPTS:
            logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)
    
    # If we get here, all retries failed
    logger.critical(f"Failed to connect to MongoDB after {MAX_RETRY_ATTEMPTS} attempts")
    detail = f"Database connection error after {MAX_RETRY_ATTEMPTS} attempts"
    if last_error:
        detail += f": {str(last_error)}"
    
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=detail
    )

# Initialize the database connection when this module is imported
initialize_db_connection()

# Dependency injection functions
def get_db():
    """Get the database instance"""
    if db is None:
        # This should only happen if the module-level initialization failed but didn't raise
        # Attempt to re-initialize
        initialize_db_connection()
    return db

def get_user_collection():
    """Get the users collection"""
    if users_collection is None:
        initialize_db_connection()
    return users_collection

def get_trips_collection():
    """Get the trips collection"""
    if trips_collection is None:
        initialize_db_connection()
    return trips_collection

async def check_db_health():
    """Health check function to verify database connectivity"""
    try:
        # Use a simple command to verify connectivity
        result = client.admin.command('ping')
        return {
            "status": "healthy",
            "database": DB_NAME,
            "ping": result.get('ok', 0) == 1
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": DB_NAME,
            "error": str(e)
        }

# Example usage in your routes:
# async def get_user(user_id: str):
#     collection = await get_user_collection()
#     return await collection.find_one({"_id": user_id}) 