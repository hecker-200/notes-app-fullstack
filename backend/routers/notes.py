"""
Notes Routes

This module contains all notes-related endpoints including
CRUD operations for notes with proper authentication.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from schemas import (
    NoteCreate, NoteUpdate, NoteResponse, NotesListResponse,
    MessageResponse, ErrorResponse, UserInDB
)
from auth import get_current_active_user
from crud import (
    create_note, get_user_notes, get_note_by_id, 
    update_note, delete_note, get_user_notes_count,
    search_user_notes
)

router = APIRouter()


@router.get(
    "/",
    response_model=NotesListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def get_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notes to return"),
    search: Optional[str] = Query(None, description="Search query for notes"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get all notes for the current user
    
    Retrieves a paginated list of notes belonging to the authenticated user.
    Optionally filters notes by search query.
    
    Args:
        skip: Number of notes to skip (for pagination)
        limit: Maximum number of notes to return
        search: Optional search query to filter notes
        current_user: Current authenticated user
    
    Returns:
        NotesListResponse with notes list and metadata
    """
    user_id = str(current_user.id)
    
    # Get notes based on search query
    if search:
        notes = await search_user_notes(user_id, search, skip, limit)
        # For search, we don't provide total count to avoid expensive operations
        total = len(notes)
    else:
        notes = await get_user_notes(user_id, skip, limit)
        total = await get_user_notes_count(user_id)
    
    return NotesListResponse(
        notes=notes,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit
    )


@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def create_new_note(
    note_data: NoteCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new note
    
    Creates a new note for the authenticated user with the provided data.
    
    Args:
        note_data: Note creation data
        current_user: Current authenticated user
    
    Returns:
        NoteResponse for the created note
    """
    try:
        note = await create_note(note_data, str(current_user.id))
        return note
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note"
        )


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Note not found"},
        400: {"model": ErrorResponse, "description": "Invalid note ID"}
    }
)
async def get_note(
    note_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get a specific note by ID
    
    Retrieves a specific note belonging to the authenticated user.
    
    Args:
        note_id: ID of the note to retrieve
        current_user: Current authenticated user
    
    Returns:
        NoteResponse for the requested note
    
    Raises:
        HTTPException: If note not found or invalid ID
    """
    note = await get_note_by_id(note_id, str(current_user.id))
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return note


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Note not found"},
        409: {"model": ErrorResponse, "description": "Version conflict - note was modified"},
        400: {"model": ErrorResponse, "description": "Invalid note ID"}
    }
)
async def update_existing_note(
    note_id: str,
    note_update: NoteUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update an existing note
    
    Updates a note belonging to the authenticated user. Supports optimistic
    concurrency control using version numbers to prevent lost updates.
    
    Args:
        note_id: ID of the note to update
        note_update: Note update data (may include version for concurrency control)
        current_user: Current authenticated user
    
    Returns:
        NoteResponse for the updated note
    
    Raises:
        HTTPException: If note not found, invalid ID, or version conflict
    """
    try:
        updated_note = await update_note(note_id, str(current_user.id), note_update)
        return updated_note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update note"
        )


@router.delete(
    "/{note_id}",
    response_model=MessageResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Note not found"},
        400: {"model": ErrorResponse, "description": "Invalid note ID"}
    }
)
async def delete_existing_note(
    note_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete a note
    
    Permanently deletes a note belonging to the authenticated user.
    
    Args:
        note_id: ID of the note to delete
        current_user: Current authenticated user
    
    Returns:
        MessageResponse confirming deletion
    
    Raises:
        HTTPException: If note not found or invalid ID
    """
    try:
        deleted = await delete_note(note_id, str(current_user.id))
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        return MessageResponse(message="Note deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note"
        )
