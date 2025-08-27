"""
CRUD Operations for Notes and Users

This module contains all database CRUD operations including
optimistic concurrency control and atomic updates.
"""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
from database import get_users_collection, get_notes_collection
from schemas import (
    UserSignUp, UserInDB, NoteCreate, NoteUpdate, 
    NoteInDB, NoteResponse
)
from auth import get_password_hash


# User CRUD Operations
async def create_user(user_data: UserSignUp) -> UserInDB:
    """
    Create a new user in the database
    
    Args:
        user_data: User registration data
    
    Returns:
        UserInDB object for the created user
    
    Raises:
        HTTPException: If email already exists
    """
    users_collection = get_users_collection()
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    try:
        result = await users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return UserInDB(**user_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


# Notes CRUD Operations
async def create_note(note_data: NoteCreate, user_id: str) -> NoteResponse:
    """
    Create a new note for a user
    
    Args:
        note_data: Note creation data
        user_id: User ID as string
    
    Returns:
        NoteResponse object for the created note
    """
    notes_collection = get_notes_collection()
    
    current_time = datetime.utcnow()
    note_doc = {
        "title": note_data.title,
        "content": note_data.content,
        "tags": note_data.tags or [],
        "is_favorite": note_data.is_favorite,
        "user_id": ObjectId(user_id),
        "created_at": current_time,
        "updated_at": current_time,
        "version": 1  # Initial version for optimistic concurrency
    }
    
    result = await notes_collection.insert_one(note_doc)
    note_doc["_id"] = result.inserted_id
    
    return NoteResponse(**note_doc)


async def get_user_notes(user_id: str, skip: int = 0, limit: int = 50) -> List[NoteResponse]:
    """
    Get all notes for a user with pagination
    
    Args:
        user_id: User ID as string
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of NoteResponse objects
    """
    notes_collection = get_notes_collection()
    
    cursor = notes_collection.find(
        {"user_id": ObjectId(user_id)}
    ).sort("created_at", -1).skip(skip).limit(limit)
    
    notes = []
    async for note_doc in cursor:
        notes.append(NoteResponse(**note_doc))
    
    return notes


async def get_note_by_id(note_id: str, user_id: str) -> Optional[NoteResponse]:
    """
    Get a specific note by ID for a user
    
    Args:
        note_id: Note ID as string
        user_id: User ID as string
    
    Returns:
        NoteResponse object if found, None otherwise
    """
    notes_collection = get_notes_collection()
    
    try:
        note_doc = await notes_collection.find_one({
            "_id": ObjectId(note_id),
            "user_id": ObjectId(user_id)
        })
        
        if note_doc:
            return NoteResponse(**note_doc)
    except Exception:
        pass
    
    return None


async def update_note(note_id: str, user_id: str, note_update: NoteUpdate) -> NoteResponse:
    """
    Update a note with optimistic concurrency control
    
    This function implements optimistic concurrency control using version numbers.
    If a version is provided in the update, it must match the current version
    in the database to prevent lost updates.
    
    Args:
        note_id: Note ID as string
        user_id: User ID as string
        note_update: Note update data
    
    Returns:
        Updated NoteResponse object
    
    Raises:
        HTTPException: If note not found or version conflict
    """
    notes_collection = get_notes_collection()
    
    try:
        # Build update document with only provided fields
        update_doc = {"updated_at": datetime.utcnow()}
        
        if note_update.title is not None:
            update_doc["title"] = note_update.title
        if note_update.content is not None:
            update_doc["content"] = note_update.content
        if note_update.tags is not None:
            update_doc["tags"] = note_update.tags
        if note_update.is_favorite is not None:
            update_doc["is_favorite"] = note_update.is_favorite
        
        # Prepare filter for the update operation
        filter_doc = {
            "_id": ObjectId(note_id),
            "user_id": ObjectId(user_id)
        }
        
        # If version is provided, include it in the filter for optimistic concurrency
        if note_update.version is not None:
            filter_doc["version"] = note_update.version
            update_doc["$inc"] = {"version": 1}  # Increment version
        else:
            update_doc["$inc"] = {"version": 1}  # Increment version
        
        # Perform atomic update
        result = await notes_collection.find_one_and_update(
            filter_doc,
            {"$set": update_doc, "$inc": update_doc.get("$inc", {})},
            return_document=True  # Return updated document
        )
        
        if result is None:
            # Check if note exists but version mismatched
            existing_note = await notes_collection.find_one({
                "_id": ObjectId(note_id),
                "user_id": ObjectId(user_id)
            })
            
            if existing_note:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Note was modified by another operation. Please refresh and try again."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Note not found"
                )
        
        return NoteResponse(**result)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )


async def delete_note(note_id: str, user_id: str) -> bool:
    """
    Delete a note (atomic operation)
    
    Args:
        note_id: Note ID as string
        user_id: User ID as string
    
    Returns:
        True if note was deleted, False if not found
    
    Raises:
        HTTPException: If invalid ID format
    """
    notes_collection = get_notes_collection()
    
    try:
        result = await notes_collection.delete_one({
            "_id": ObjectId(note_id),
            "user_id": ObjectId(user_id)
        })
        
        return result.deleted_count > 0
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note ID format"
        )


async def get_user_notes_count(user_id: str) -> int:
    """
    Get total count of notes for a user
    
    Args:
        user_id: User ID as string
    
    Returns:
        Total number of notes for the user
    """
    notes_collection = get_notes_collection()
    
    count = await notes_collection.count_documents({
        "user_id": ObjectId(user_id)
    })
    
    return count


async def search_user_notes(user_id: str, search_query: str, skip: int = 0, limit: int = 50) -> List[NoteResponse]:
    """
    Search notes for a user by title or content
    
    Args:
        user_id: User ID as string
        search_query: Text to search for
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of matching NoteResponse objects
    """
    notes_collection = get_notes_collection()
    
    # Create text search query
    filter_doc = {
        "user_id": ObjectId(user_id),
        "$or": [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"content": {"$regex": search_query, "$options": "i"}},
            {"tags": {"$in": [{"$regex": search_query, "$options": "i"}]}}
        ]
    }
    
    cursor = notes_collection.find(filter_doc).sort("created_at", -1).skip(skip).limit(limit)
    
    notes = []
    async for note_doc in cursor:
        notes.append(NoteResponse(**note_doc))
    
    return notes
