# =======================
# app/interfaces/storage_provider.py
# =======================
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class StorageProvider(ABC):
    """Abstract interface for file storage operations."""
    
    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file: BinaryIO,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file and return public URL."""
        pass
    
    @abstractmethod
    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """Download file content."""
        pass
    
    @abstractmethod
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file."""
        pass
    
    @abstractmethod
    async def get_signed_url(
        self, 
        bucket: str, 
        file_path: str, 
        expires_in: int = 3600
    ) -> str:
        """Get signed URL for private file access."""
        pass
    
    @abstractmethod
    async def file_exists(self, bucket: str, file_path: str) -> bool:
        """Check if file exists."""
        pass


