# =======================
# app/api/v1/users.py
# =======================
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_user_service
from app.services.user_service import UserService
from app.models.user import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a new user."""
    try:
        user = await user_service.create_user(request)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Get user by ID."""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Update user information."""
    try:
        # Implementation would call user_service.update_user
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

