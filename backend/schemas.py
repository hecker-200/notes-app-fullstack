"""
Pydantic Schemas for Request/Response Validation

This module contains all Pydantic models used for request validation,
response serialization, and data transfer objects (DTOs).
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic models
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# User Schemas
class UserSignUp(BaseModel):
    """
    Schema for user registration request
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")
    full_name: Optional[str] = Field(None, description="User full name")


class UserLogin(BaseModel):
    """
    Schema for user login request
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """
    Schema for user data in responses
    """
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime
    is_active: bool = True


class UserInDB(UserResponse):
    """
    Schema for user data as stored in database (includes hashed password)
    """
    hashed_password: str


# Authentication Schemas
class Token(BaseModel):
    """
    Schema for JWT token response
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """
    Schema for token payload data
    """
    user_id: Optional[str] = None
    email: Optional[str] = None


# Note Schemas
class NoteCreate(BaseModel):
    """
    Schema for creating a new note
    """
    title: str = Field(..., max_length=200, description="Note title")
    content: str = Field(..., description="Note content/body")
    tags: Optional[List[str]] = Field(default_factory=list, description="Note tags")
    is_favorite: bool = Field(default=False, description="Whether note is marked as favorite")


class NoteUpdate(BaseModel):
    """
    Schema for updating an existing note
    """
    title: Optional[str] = Field(None, max_length=200, description="Note title")
    content: Optional[str] = Field(None, description="Note content/body")
    tags: Optional[List[str]] = Field(None, description="Note tags")
    is_favorite: Optional[bool] = Field(None, description="Whether note is marked as favorite")
    version: Optional[int] = Field(None, description="Version number for optimistic concurrency control")


class NoteResponse(BaseModel):
    """
    Schema for note data in responses
    """
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    is_favorite: bool = False
    user_id: PyObjectId
    created_at: datetime
    updated_at: datetime
    version: int = Field(default=1, description="Version number for optimistic concurrency control")


class NoteInDB(NoteResponse):
    """
    Schema for note data as stored in database
    """
    pass


# Response Schemas
class MessageResponse(BaseModel):
    """
    Schema for simple message responses
    """
    message: str


class ErrorResponse(BaseModel):
    """
    Schema for error responses
    """
    detail: str
    error_code: Optional[str] = None


class NotesListResponse(BaseModel):
    """
    Schema for notes list response with metadata
    """
    notes: List[NoteResponse]
    total: int
    page: int = 1
    per_page: int = 50


# Authentication response with user info
class AuthResponse(BaseModel):
    """
    Schema for authentication response including user data and token
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
