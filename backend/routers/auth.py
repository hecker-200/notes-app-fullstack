"""
Authentication Routes

This module contains authentication-related endpoints including
user signup, login, and token management.
"""

from datetime import timedelta #this is to set time for jwt token expiration
from fastapi import APIRouter, HTTPException, status, Depends #basically for the routing
# and to manage dependecies and handle errors
from schemas import (
    UserSignUp, UserLogin, AuthResponse, UserResponse, 
    MessageResponse, ErrorResponse
)  #these are models that we have defined basically in our schemas.py folder which are pydantic models
# have different functionalities
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
) # these are the functions for authentication from auth.py
from crud import create_user #this is basically one of the 4 functions to create user from crud

router = APIRouter() # this basically acts as the main point of entry or call for the routing purpose
#similar to express in mern

# this is for the signup route when we  click signup
@router.post( 
    "/signup",
    response_model=AuthResponse, # the model that we take here is the auth response one
    responses={
        400: {"model": ErrorResponse, "description": "Email already registered"}, #we will  throw 400 
        #422 error based on the type of error
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
        
        # Create access token this also puts time = time delta as the access token expiry 
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, # this is the payload for the jwt here we are using id as the payload
            expires_delta=access_token_expires
        )
        
        # Prepare user response (exclude sensitive data)

        #here we are taking different fields basedon the input  of the user
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            is_active=user.is_active
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer", #this is basically showing that it is the bearer of the token that it is a part of
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_response
        )
        
    except HTTPException: #this is again a part of try catch only incase this error pops up here we re raise it
        raise
    except Exception as e: # this is where any unexpected error is caught like db errors or stack traces
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
    #defined in auth.py function and fr
    user = await authenticate_user(user_credentials.email, user_credentials.password)
    
    if not user: #if ew dont get any response then this error is raised
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}, # this is a method that is used to raise 401 error
            #basically telling that this is the method to authenticate and only authenticate bearer
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
