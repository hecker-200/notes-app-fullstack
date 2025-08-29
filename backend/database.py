"""
Database Configuration and Connection Management

This module is responsible for:
1. Managing the MongoDB connection (using Motor, the async driver for MongoDB).
2. Initializing and storing a reference to the database.
3. Creating required indexes for collections (users, notes).
4. Exposing helper functions to access specific collections (users, notes).

It ensures that:
- The database connection is established before the app starts serving requests.
- The connection is cleanly closed when the app shuts down.
- Indexes are created upfront for query performance and data integrity.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

# -------------------------
# Logging setup
# -------------------------
# Configure logging so that any database connection activity
# (success, failure, disconnection, etc.) gets reported in the logs.
# This helps during debugging and in production monitoring.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Database Configuration
# -------------------------
# Connection URL for MongoDB. By default, it connects to a local instance,
# but in production, this should come from environment variables (like Atlas or Docker).
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

# Name of the database that will store all collections.
DATABASE_NAME = os.getenv("DATABASE_NAME", "notes_app")

# -------------------------
# Global Client + Database
# -------------------------
# These variables will be initialized when the app starts
# so we can reuse the same MongoDB client instance across the app.
# (MongoDB drivers handle pooling internally, so creating multiple clients is inefficient.)
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """
    Create a connection to MongoDB and set up the database instance.

    Steps:
    1. Initialize the MongoDB client with the provided connection string.
    2. Run the 'ismaster' command to confirm the server is reachable.
    3. Store the database instance globally for app-wide use.
    4. Create indexes to enforce uniqueness and improve performance.

    Raises:
        ConnectionFailure: If the database server cannot be reached.
    """
    global client, database
    try:
        # Initialize the async MongoDB client
        client = AsyncIOMotorClient(MONGODB_URL)

        # Run a simple command to check if the connection is alive
        # 'ismaster' is a lightweight operation that doesn't require authentication
        await client.admin.command('ismaster')

        # Get reference to the app database (like schema in SQL)
        database = client[DATABASE_NAME]

        logger.info(f"✅ Successfully connected to MongoDB at {MONGODB_URL}")

        # Set up required indexes (unique constraints, performance improvements)
        await create_indexes()

    except ConnectionFailure as e:
        # Log and re-raise the error if the connection fails
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise e


async def close_mongo_connection():
    """
    Close the MongoDB connection when the application shuts down.

    This ensures:
    - The client properly releases resources.
    - We don't leave open connections, which can cause issues if the app restarts.
    """
    global client
    if client:
        client.close()
        logger.info("🔌 Disconnected from MongoDB")


async def create_indexes():
    """
    Create necessary database indexes for performance and integrity.

    Indexes used:
    1. Users collection:
       - Unique index on 'email' to ensure no duplicate registrations.
    2. Notes collection:
       - Index on 'user_id' to quickly fetch notes by user.
       - Compound index on (user_id, created_at) for queries like:
         "get the most recent notes for this user."

    Benefits:
    - Enforces data consistency (unique email).
    - Makes queries faster by reducing scan time.
    """
    try:
        # Users: prevent duplicate email registrations
        await database.users.create_index("email", unique=True)

        # Notes: allow fast lookup of notes belonging to a specific user
        await database.notes.create_index("user_id")

        # Notes: allow efficient queries sorted by creation time (per user)
        await database.notes.create_index([("user_id", 1), ("created_at", -1)])

        logger.info("📑 Database indexes created successfully")

    except Exception as e:
        # Not fatal, but log if something goes wrong during index creation
        logger.warning(f"⚠️ Failed to create indexes: {e}")


def get_database():
    """
    Get the database instance.

    This allows other parts of the app (routes, services, CRUD modules)
    to access the MongoDB database without needing to re-import or recreate the client.
    """
    return database


# -------------------------
# Collection Shortcuts
# -------------------------
# These helper functions provide easy access to specific collections
# (users and notes) without needing to manually fetch them everywhere.

def get_users_collection():
    """
    Get the 'users' collection object from the database.
    
    Returns:
        Motor async collection object for users.
    """
    return database.users


def get_notes_collection():
    """
    Get the 'notes' collection object from the database.
    
    Returns:
        Motor async collection object for notes.
    """
    return database.notes
