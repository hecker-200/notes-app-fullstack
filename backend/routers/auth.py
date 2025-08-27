"""
Authentication Routes

This module contains authentication-related endpoints including
user signup, login, and token management.
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from schemas import (
    UserSignUp, UserLogin, AuthResponse, UserResponse, 
    MessageResponse, ErrorResponse
)
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from crud import create_user

router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def signup(user_data: UserSignUp):
    """
    Register a new user account
    
    Creates a new user with the provided email and password.
    Returns JWT token for immediate authentication.
    
    Args:
        user_data: User registration information
    
    Returns:
        AuthResponse with JWT token and user information
    
    Raises:
        HTTPException: If email is already registered
    """
    try:
        # Create new user in database
        user = await create_user(user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Prepare user response (exclude sensitive data)
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def login(user_credentials: UserLogin):
    """
    Authenticate user and return JWT token
    
    Validates user credentials and returns a JWT token for API access.
    
    Args:
        user_credentials: User login information (email and password)
    
    Returns:
        AuthResponse with JWT token and user information
    
    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user credentials
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Prepare user response (exclude sensitive data)
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        is_active=user.is_active
    )
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user=user_response
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        400: {"model": ErrorResponse, "description": "Inactive user"}
    }
)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """
    Get current authenticated user information
    
    This endpoint allows clients to retrieve information about the
    currently authenticated user using their JWT token.
    
    Args:
        current_user: Current authenticated user (from JWT token)
    
    Returns:
        UserResponse with current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )
