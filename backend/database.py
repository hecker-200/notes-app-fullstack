"""
Database Configuration and Connection Management

This module handles MongoDB connection, database initialization,
and provides database instances for the application.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "notes_app")

# Global database client and database instances
client: AsyncIOMotorClient = None
database = None


async def connect_to_mongo():
    """
    Create database connection and initialize database instance
    """
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        # Test the connection
        await client.admin.command('ismaster')
        database = client[DATABASE_NAME]
        logger.info(f"Successfully connected to MongoDB at {MONGODB_URL}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e


async def close_mongo_connection():
    """
    Close database connection
    """
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """
    Create database indexes for optimal query performance
    """
    try:
        # Create unique index on user email
        await database.users.create_index("email", unique=True)
        
        # Create index on notes user_id for faster queries
        await database.notes.create_index("user_id")
        
        # Create compound index for user notes with creation time
        await database.notes.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")


def get_database():
    """
    Get the database instance
    Returns the database connection for use in route handlers
    """
    return database


# Collections shortcuts
def get_users_collection():
    """Get users collection"""
    return database.users


def get_notes_collection():
    """Get notes collection"""
    return database.notes
