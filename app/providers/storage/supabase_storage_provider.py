# =======================
# app/providers/storage/supabase_storage_provider.py
# =======================
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, BinaryIO
import structlog

from supabase import Client
from app.interfaces.storage_provider import StorageProvider
from app.core.exceptions import AppException

logger = structlog.get_logger()


class SupabaseStorageProvider(StorageProvider):
    """Supabase storage provider implementation."""
    
    def __init__(self, client: Client):
        self.client = client
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file: BinaryIO,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file and return public URL."""
        def _upload():
            try:
                # Read file content
                file_content = file.read()
                
                # Upload to Supabase storage
                response = self.client.storage.from_(bucket).upload(
                    file_path,
                    file_content,
                    file_options={"content-type": content_type} if content_type else None
                )
                
                # Get public URL
                public_url = self.client.storage.from_(bucket).get_public_url(file_path)
                return public_url
            except Exception as e:
                logger.error(f"Error uploading file to {bucket}", error=str(e), file_path=file_path)
                raise AppException(f"Storage error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _upload)
    
    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """Download file content."""
        def _download():
            try:
                response = self.client.storage.from_(bucket).download(file_path)
                return response
            except Exception as e:
                logger.error(f"Error downloading file from {bucket}", error=str(e), file_path=file_path)
                raise AppException(f"Storage error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _download)
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete file."""
        def _delete():
            try:
                response = self.client.storage.from_(bucket).remove([file_path])
                return len(response) > 0
            except Exception as e:
                logger.error(f"Error deleting file from {bucket}", error=str(e), file_path=file_path)
                raise AppException(f"Storage error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _delete)
    
    async def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """Get signed URL for private file access."""
        def _get_url():
            try:
                response = self.client.storage.from_(bucket).create_signed_url(
                    file_path, expires_in
                )
                return response['signedURL']
            except Exception as e:
                logger.error(f"Error creating signed URL for {bucket}", error=str(e), file_path=file_path)
                raise AppException(f"Storage error: {str(e)}")
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_url)
    
    async def file_exists(self, bucket: str, file_path: str) -> bool:
        """Check if file exists."""
        def _exists():
            try:
                # Try to get file info
                response = self.client.storage.from_(bucket).list(path=file_path)
                return len(response) > 0
            except Exception:
                return False
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _exists)
