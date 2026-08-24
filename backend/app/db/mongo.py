"""
MongoDB connection layer for SolSight.
Uses Motor (async driver) so FastAPI route handlers can await DB calls directly.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "solsight")

client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
panels_collection = db["panels"]
inspections_collection = db["inspections"]


async def ensure_indexes():
    """Create indexes needed for fast lookups. Call once on app startup."""
    await users_collection.create_index("email", unique=True)
    await panels_collection.create_index("panel_id", unique=True)
    await inspections_collection.create_index("panel_id")
    await inspections_collection.create_index([("panel_id", 1), ("created_at", 1)])