from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine, Base
import app.models.entities
from app.routers import auth, students, jobs, applications

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="PlacementHub API",
    version="1.0.0",
    description="Campus Placement Management System Backend",
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(jobs.router)
app.include_router(applications.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": "PlacementHub",
        "database": "connected"
    }
