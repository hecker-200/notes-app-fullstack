"""
FastAPI Notes App - Main Application Entry Point

This file is the **entry point** of the Notes API application.

Responsibilities:
1. Create the FastAPI application instance.
2. Configure middleware (e.g., CORS for frontend communication).
3. Handle application lifecycle events (startup/shutdown).
4. Register routers for modular endpoints (authentication + notes).
5. Provide a health check root endpoint for testing availability.

In short: This is the file that ties everything together.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import close_mongo_connection, connect_to_mongo
from routers import auth, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    FastAPI allows defining a lifespan function that runs code:
      - BEFORE the application starts serving requests (startup).
      - AFTER the application finishes (shutdown).

    Here’s what we do:
    - On startup: Connect to MongoDB so the app has a working DB connection.
    - On shutdown: Gracefully close the MongoDB connection to free resources.

    Using `@asynccontextmanager` makes this clean and ensures
    both startup and shutdown logic are neatly paired together.
    """
    # ------------------------
    # Startup logic
    # ------------------------
    await connect_to_mongo()  # Create DB client, test connection, build indexes
    
    # Yield control back to FastAPI (the app runs here in between)
    yield
    
    # ------------------------
    # Shutdown logic
    # ------------------------
    await close_mongo_connection()  # Release DB resources, close connections


# ------------------------
# FastAPI App Initialization
# ------------------------
# Create the main application object.
# - `title`, `description`, and `version` appear in auto-generated docs (/docs, /redoc).
# - `lifespan` links our startup/shutdown manager to the app.
app = FastAPI(
    title="Notes API",
    description="A simple notes API with JWT authentication",
    version="1.0.0",
    lifespan=lifespan
)


# ------------------------
# Middleware Configuration
# ------------------------
# Middleware is software that processes requests before they reach your routes
# or processes responses before sending them back.
#
# Here, we configure CORS (Cross-Origin Resource Sharing) so that the
# React frontend (running on localhost:5173) can talk to the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin (React dev server)
    allow_credentials=True,                   # Allow cookies/headers like Authorization
    allow_methods=["*"],                      # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],                      # Allow all headers in requests
)


# ------------------------
# Health Check Endpoint
# ------------------------
@app.get("/")
async def root():
    """
    Root endpoint for health check.
    
    Purpose:
    - Quick sanity test to confirm the API is running.
    - Returns a simple JSON message.
    - Useful for Kubernetes/Docker liveness probes or manual checks.
    """
    return {"message": "Notes API is running!"}


# ------------------------
# Router Registration
# ------------------------
# Routers keep the code modular by grouping related endpoints.
# - Authentication endpoints (login, signup, token verification).
# - Notes endpoints (CRUD operations for user notes).

# All authentication routes will be available under `/auth/...`
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# All notes routes will be available under `/notes/...`
app.include_router(notes.router, prefix="/notes", tags=["notes"])


# ------------------------
# Run the App (only if executed directly)
# ------------------------
# If you run this file directly with `python main.py`, it will start uvicorn.
# Normally, in production, you'd use `uvicorn main:app --reload` from the terminal.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
