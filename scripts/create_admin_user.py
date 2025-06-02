# =======================
# scripts/create_admin_user.py
# =======================
"""
Script to create an admin user.
"""
import asyncio
import sys

from app.core.config import get_settings
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.providers.database.supabase_provider import SupabaseProvider
from app.models.user import UserCreateRequest, UserType

async def create_admin_user(email: str):
    """Create an admin user."""
    print(f"👤 Creating admin user: {email}")
    
    settings = get_settings()
    db_provider = SupabaseProvider(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    user_repo = UserRepository(db_provider)
    user_service = UserService(user_repo)
    
    try:
        request = UserCreateRequest(
            email=email,
            user_type=UserType.ADMIN,
            preferences={"role": "administrator"}
        )
        
        user = await user_service.create_user(request)
        print(f"✅ Admin user created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Type: {user.user_type}")
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_admin_user.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(create_admin_user(email))

