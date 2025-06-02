"""FastAPI dependencies."""

from typing import Generator
from fastapi import Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from app.core.container import Container
from app.services.user_service import UserService


async def get_database():
    """Get database connection."""
    # This would be implemented based on your database provider
    pass


@inject
async def get_current_user(
    user_service: UserService = Depends(Provide[Container.user_service])
):
    """Get current authenticated user."""
    # This would be implemented based on your authentication strategy
    # For now, returning a placeholder
    pass


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get current active user."""
    # Add user active status check here
    return current_user
