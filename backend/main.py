"""
FastAPI Notes App - Main Application Entry Point

This is the main FastAPI application that sets up CORS, includes routers,
and handles the application startup/shutdown events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import close_mongo_connection, connect_to_mongo
from routers import auth, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    """
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


# Create FastAPI application instance
app = FastAPI(
    title="Notes API",
    description="A simple notes API with JWT authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """
    Root endpoint for health check
    """
    return {"message": "Notes API is running!"}


# Include authentication routes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include notes routes
app.include_router(notes.router, prefix="/notes", tags=["notes"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
