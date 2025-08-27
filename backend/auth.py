"""
Authentication Utilities

This module handles JWT token creation/validation, password hashing,
and authentication middleware for protected routes.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_users_collection
from schemas import TokenData, UserInDB
from bson import ObjectId

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a hash from a plain password
    
    Args:
        password: Plain text password to hash
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing token payload data
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Retrieve user from database by email
    
    Args:
        email: User email address
    
    Returns:
        UserInDB object if found, None otherwise
    """
    users_collection = get_users_collection()
    user_data = await users_collection.find_one({"email": email})
    
    if user_data:
        return UserInDB(**user_data)
    return None


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """
    Retrieve user from database by ID
    
    Args:
        user_id: User ObjectId as string
    
    Returns:
        UserInDB object if found, None otherwise
    """
    users_collection = get_users_collection()
    
    try:
        user_data = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return UserInDB(**user_data)
    except Exception:
        pass
    
    return None


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user credentials
    
    Args:
        email: User email
        password: Plain text password
    
    Returns:
        UserInDB object if authentication successful, None otherwise
    """
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Get current authenticated user from JWT token
    
    This dependency can be used in route handlers to ensure authentication
    and get the current user information.
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        UserInDB object for the authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Get current authenticated and active user
    
    This dependency ensures the user is both authenticated and active.
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        UserInDB object for the authenticated active user
    
    Raises:
        HTTPException: If user account is disabled
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user
