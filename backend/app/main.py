import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import mongo
from app.demo_data import seed_demo_fleet
from app.deps import WORKSPACE_OWNER
from app.routers import panels, inspections
from app.services.prediction_service import prediction_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("solsight")

# Comma-separated list, e.g. "http://localhost:5173,https://solsight.example.com"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await mongo.ensure_indexes()
        # In-memory mode starts empty on every boot; give it something to show.
        if mongo.IN_MEMORY and os.getenv("SEED_DEMO_FLEET", "true").lower() == "true":
            await seed_demo_fleet(mongo.panels_collection, mongo.inspections_collection, WORKSPACE_OWNER["email"])
    except Exception as e:
        # Don't refuse to boot -- /health will report the database as down.
        log.error("database not reachable at startup: %s", e)
    yield


app = FastAPI(
    title="SolSight API",
    description="Solar panel defect detection, health monitoring, and degradation prediction.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(panels.router)
app.include_router(inspections.router)


@app.get("/")
async def root():
    return {"service": "SolSight API", "status": "running"}


@app.get("/health")
async def health_check():
    db_ok = await mongo.ping()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "in-memory" if mongo.IN_MEMORY else ("up" if db_ok else "down"),
        "models_trained": prediction_service.trained,
    }
