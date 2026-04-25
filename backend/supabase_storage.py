"""
Supabase Storage Integration Module
Handles file uploads, deletions, and signed URL generation for the Map-files bucket.
"""

import os
import uuid
import logging
from typing import Optional
from werkzeug.utils import secure_filename

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError("supabase-py is required. Install with: pip install supabase")

log = logging.getLogger(__name__)


class SupabaseStorageManager:
    """
    Manages file uploads to Supabase Storage with the following path structure:
    {user_id}/{feature_name}/{item_id}/{uuid}.{extension}
    
    Examples:
    - 123/alerts/456/abc123def-ef12-abcd-ef12-abcdef123456.jpg
    - 123/profile/avatar/xyz789abc-fe34-5678-ab90-cdef12345678.png
    """
    
    BUCKET_NAME = os.getenv('SUPABASE_STORAGE_BUCKET', 'Map-files')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[-1].lower()
        return ext in SupabaseStorageManager.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract file extension."""
        if not filename or '.' not in filename:
            return 'bin'
        return secure_filename(filename).rsplit('.', 1)[-1].lower()
    
    def upload_file(
        self, 
        file,
        user_id: int,
        feature_name: str,
        item_id: Optional[int] = None,
        cache_control: str = '3600'
    ) -> dict:
        """
        Upload a file to Supabase Storage.
        
        Args:
            file: File object from Flask request.files
            user_id: User ID (from JWT)
            feature_name: Feature name (e.g., 'alerts', 'profile')
            item_id: Item ID (e.g., alert_id, optional for avatars)
            cache_control: Cache control header
        
        Returns:
            Dictionary with 'path' key containing the storage path
        
        Raises:
            ValueError: If file is invalid or upload fails
        """
        if not file or file.filename == '':
            raise ValueError("No file provided")
        
        if not self.allowed_file(file.filename):
            raise ValueError(
                f"File extension not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # Build storage path: {user_id}/{feature_name}/{item_id}/{uuid}.{ext}
        file_ext = self.get_file_extension(file.filename)
        file_uuid = str(uuid.uuid4())
        
        if item_id:
            storage_path = f"{user_id}/{feature_name}/{item_id}/{file_uuid}.{file_ext}"
        else:
            # For items without IDs (e.g., avatar), use a fixed name
            storage_path = f"{user_id}/{feature_name}/{file_uuid}.{file_ext}"
        
        try:
            # Read file content
            file_content = file.read()
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    'cacheControl': cache_control,
                    'contentType': file.content_type or 'application/octet-stream'
                }
            )
            
            log.info(f"File uploaded successfully: {storage_path}")
            return {'path': storage_path}
        
        except Exception as e:
            log.error(f"Supabase upload error: {str(e)}")
            raise ValueError(f"Failed to upload file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            file_path: Full storage path (e.g., "123/alerts/456/abc123.jpg")
        
        Returns:
            True if successful, False otherwise
        """
        if not file_path:
            return False
        
        try:
            self.client.storage.from_(self.BUCKET_NAME).remove([file_path])
            log.info(f"File deleted successfully: {file_path}")
            return True
        except Exception as e:
            log.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_signed_url(
        self, 
        file_path: str, 
        expires_in: int = 3600
    ) -> dict:
        """
        Generate a signed URL for a file in the private bucket.
        
        Args:
            file_path: Full storage path (e.g., "123/alerts/456/abc123.jpg")
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Dictionary with 'signed_url' key
        
        Raises:
            ValueError: If URL generation fails
        """
        if not file_path:
            raise ValueError("File path is required")
        
        try:
            response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            
            if response.get('error'):
                raise ValueError(response['error'].get('message', 'Unknown error'))
            
            signed_url = response.get('signedURL') or response.get('signed_url')
            if not signed_url:
                raise ValueError("No signed URL returned")
            
            log.info(f"Signed URL created for: {file_path}")
            return {'signed_url': signed_url}
        
        except Exception as e:
            log.error(f"Error creating signed URL for {file_path}: {str(e)}")
            raise ValueError(f"Failed to create signed URL: {str(e)}")


# Global instance
_storage_manager = None

def get_storage_manager() -> SupabaseStorageManager:
    """Get or create the Supabase Storage Manager singleton."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = SupabaseStorageManager()
    return _storage_manager
