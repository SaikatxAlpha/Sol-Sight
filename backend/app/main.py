from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongo import ensure_indexes
from app.routers import auth, panels, inspections

app = FastAPI(
    title="SolSight API",
    description="AI-powered solar panel defect detection, health monitoring, and degradation prediction.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(panels.router)
app.include_router(inspections.router)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()


@app.get("/")
async def root():
    return {"service": "SolSight API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}