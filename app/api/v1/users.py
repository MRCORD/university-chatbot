"""User management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from app.core.container import Container
from app.models.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse)
@inject
async def create_user(
    user: UserCreate,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    """Create a new user."""
    try:
        response = await user_service.create_user(user)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
@inject
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    """List all users."""
    try:
        users = await user_service.list_users(skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
@inject
async def get_user(
    user_id: str,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    """Get user by ID."""
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
@inject
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    user_service: UserService = Depends(Provide[Container.user_service])
):
    """Update user information."""
    try:
        user = await user_service.update_user(user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )
