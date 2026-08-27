"""
Seed (or reset) a permanent admin account in SolSight's MongoDB so you
don't have to register a new user every time you wipe the database.

Place this file at: backend/seed_admin.py
Run it from the backend/ directory (with your venv activated):

    python seed_admin.py

Default credentials created:
    email:    admin@solsight.com
    password: admin123

Change ADMIN_EMAIL / ADMIN_PASSWORD below if you want different ones.
Safe to re-run any time -- it upserts, so it won't create duplicates,
and it will reset the password if the record already exists.
"""
import asyncio
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "solsight")

ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@solsight.com"
ADMIN_PASSWORD = "admin123"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db["users"]

    hashed = pwd_context.hash(ADMIN_PASSWORD)

    existing = await users_collection.find_one({"email": ADMIN_EMAIL})
    if existing:
        await users_collection.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"name": ADMIN_NAME, "hashed_password": hashed}},
        )
        print(f"Admin user already existed -- password reset for {ADMIN_EMAIL}")
    else:
        await users_collection.insert_one({
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "hashed_password": hashed,
            "created_at": datetime.utcnow(),
        })
        print(f"Admin user created: {ADMIN_EMAIL}")

    print(f"Login with:\n  email:    {ADMIN_EMAIL}\n  password: {ADMIN_PASSWORD}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_admin())