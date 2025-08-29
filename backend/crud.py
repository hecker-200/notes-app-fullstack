"""
CRUD Operations for Notes and Users

This module contains all database CRUD operations including:
- User account creation with password hashing
- Note creation, reading, updating, and deletion
- Optimistic concurrency control using version numbers (prevents overwriting changes from another session)
- Atomic operations (ensuring MongoDB executes updates/deletes safely in a single step)
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


# =====================================================
# USER CRUD OPERATIONS
# =====================================================

async def create_user(user_data: UserSignUp) -> UserInDB:
    """
    Create a new user in the database.
    
    Detailed Flow:
    - Receives a UserSignUp object (email, password, full name).
    - Checks if a user with the same email already exists.
    - If unique, hashes the password before saving (NEVER store plain text).
    - Inserts a new user document with timestamps and "is_active" flag.
    - Returns the newly created user wrapped in a UserInDB schema.
    - If email already exists → raises 400 BAD REQUEST.
    """
    users_collection = get_users_collection()
    
    # 1. Check for duplicate email
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 2. Build user document (hashed password for security!)
    user_doc = {
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    try:
        # 3. Insert user into DB
        result = await users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return UserInDB(**user_doc)
    except DuplicateKeyError:
        # 4. Handle edge-case of race condition: two users signing up same email simultaneously
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )


# =====================================================
# NOTES CRUD OPERATIONS
# =====================================================

async def create_note(note_data: NoteCreate, user_id: str) -> NoteResponse:
    """
    Create a new note for a specific user.
    
    Detailed Flow:
    - Takes note input (title, content, tags, favorite flag).
    - Attaches the note to a user by user_id.
    - Initializes `created_at` and `updated_at`.
    - Sets an initial version = 1 (used for concurrency control later).
    - Inserts into DB, returns the saved note wrapped as NoteResponse.
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
        "version": 1  # Start at version 1 for optimistic concurrency
    }
    
    result = await notes_collection.insert_one(note_doc)
    note_doc["_id"] = result.inserted_id
    
    return NoteResponse(**note_doc)


async def get_user_notes(user_id: str, skip: int = 0, limit: int = 50) -> List[NoteResponse]:
    """
    Fetch all notes belonging to a user with pagination.
    
    Detailed Flow:
    - Finds all notes that belong to the given user_id.
    - Applies sorting (newest first by created_at).
    - Applies skip/limit for pagination.
    - Iterates through results and converts to NoteResponse objects.
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
    Fetch a single note by its ID, only if it belongs to the given user.
    
    Detailed Flow:
    - Looks up a note where _id matches note_id AND user_id matches.
    - This ensures a user cannot access another user’s notes.
    - If found, wraps into NoteResponse; otherwise returns None.
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
        # Could fail if note_id is not a valid ObjectId
        pass
    
    return None


async def update_note(note_id: str, user_id: str, note_update: NoteUpdate) -> NoteResponse:
    """
    Update a note using optimistic concurrency control (OCC).
    
    Why OCC?
    - Imagine 2 sessions editing the same note at once.
    - Without OCC, the last writer overwrites the other → "lost update" problem.
    - With OCC, updates must include the correct version number.
    - If the version doesn’t match DB, a 409 Conflict is raised.
    
    Detailed Flow:
    - Builds an update_doc with only provided fields.
    - Sets new updated_at timestamp.
    - If a version is included, it’s added to the filter query (ensuring OCC).
    - Uses atomic `find_one_and_update` so DB guarantees only one succeeds.
    - If no match found → either note doesn’t exist OR version mismatch.
    - Returns updated note if successful.
    """
    notes_collection = get_notes_collection()
    
    try:
        # 1. Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if note_update.title is not None:
            update_doc["title"] = note_update.title
        if note_update.content is not None:
            update_doc["content"] = note_update.content
        if note_update.tags is not None:
            update_doc["tags"] = note_update.tags
        if note_update.is_favorite is not None:
            update_doc["is_favorite"] = note_update.is_favorite
        
        # 2. Filter: must match correct note_id + user_id
        filter_doc = {
            "_id": ObjectId(note_id),
            "user_id": ObjectId(user_id)
        }
        
        # 3. Enforce optimistic concurrency: match version too if provided
        if note_update.version is not None:
            filter_doc["version"] = note_update.version
            update_doc["$inc"] = {"version": 1}
        else:
            update_doc["$inc"] = {"version": 1}
        
        # 4. Perform atomic update
        result = await notes_collection.find_one_and_update(
            filter_doc,
            {"$set": update_doc, "$inc": update_doc.get("$inc", {})},
            return_document=True  # Ask DB to return updated document
        )
        
        if result is None:
            # 5. Determine why update failed
            existing_note = await notes_collection.find_one({
                "_id": ObjectId(note_id),
                "user_id": ObjectId(user_id)
            })
            
            if existing_note:
                # Note exists but version mismatch → conflict
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Note was modified by another operation. Please refresh and try again."
                )
            else:
                # Note does not exist at all
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
    Delete a note (atomic).
    
    Detailed Flow:
    - Tries to delete a note with both note_id and user_id.
    - Ensures users can delete only their own notes.
    - Returns True if deleted, False if not found.
    - Raises 400 if note_id is not valid.
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
    Count how many notes a user owns.
    
    Useful for:
    - Dashboards
    - Quotas / limits
    - Analytics
    
    Detailed Flow:
    - Runs a count_documents query filtered by user_id.
    - Returns integer count.
    """
    notes_collection = get_notes_collection()
    
    count = await notes_collection.count_documents({
        "user_id": ObjectId(user_id)
    })
    
    return count


async def search_user_notes(user_id: str, search_query: str, skip: int = 0, limit: int = 50) -> List[NoteResponse]:
    """
    Search notes for a user by keyword.
    
    Detailed Flow:
    - Matches notes that belong to the user.
    - Performs case-insensitive regex search on:
        • Title
        • Content
        • Tags
    - Applies skip/limit for pagination.
    - Returns results as NoteResponse list.
    """
    notes_collection = get_notes_collection()
    
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
