"""Google Drive integration for importing meeting notes."""
import os
from typing import List, Dict, Any, Optional

# Google API client libraries
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GoogleDriveClient:
    """Client for Google Drive operations."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly',
    ]
    
    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """Initialize with OAuth credentials."""
        self.credentials = credentials
        self._service = None
    
    def _get_service(self):
        """Get or create Drive API service."""
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API client libraries not installed")
        
        if self._service is None:
            if not self.credentials:
                raise Exception("No credentials provided")
            
            creds = Credentials(
                token=self.credentials.get('access_token'),
                refresh_token=self.credentials.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('OAUTH_CLIENT_ID'),
                client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
            )
            self._service = build('drive', 'v3', credentials=creds)
        
        return self._service
    
    def list_files(
        self,
        folder_id: Optional[str] = None,
        mime_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List files in Drive.
        
        Args:
            folder_id: Optional folder ID to list files from
            mime_types: Filter by MIME types (e.g., ['text/plain', 'application/vnd.google-apps.document'])
            limit: Maximum number of files to return
        
        Returns:
            List of file metadata dictionaries
        """
        service = self._get_service()
        
        # Build query
        query_parts = ["trashed = false"]
        
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        if mime_types:
            mime_query = " or ".join([f"mimeType = '{mt}'" for mt in mime_types])
            query_parts.append(f"({mime_query})")
        
        query = " and ".join(query_parts)
        
        # Execute request
        results = service.files().list(
            q=query,
            pageSize=limit,
            fields="files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)",
            orderBy="modifiedTime desc"
        ).execute()
        
        return results.get('files', [])
    
    def list_meeting_notes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List files that are likely meeting notes.
        Filters for text documents and Google Docs.
        """
        mime_types = [
            'text/plain',
            'text/markdown',
            'application/vnd.google-apps.document',
        ]
        return self.list_files(mime_types=mime_types, limit=limit)
    
    def get_file_content(self, file_id: str) -> str:
        """
        Download and return file content as text.
        Handles both regular files and Google Docs.
        """
        service = self._get_service()
        
        # Get file metadata
        file_meta = service.files().get(fileId=file_id, fields='mimeType').execute()
        mime_type = file_meta.get('mimeType', '')
        
        if mime_type == 'application/vnd.google-apps.document':
            # Export Google Doc as plain text
            content = service.files().export(
                fileId=file_id,
                mimeType='text/plain'
            ).execute()
            return content.decode('utf-8') if isinstance(content, bytes) else content
        else:
            # Download regular file
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.seek(0)
            return fh.read().decode('utf-8')
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get metadata for a specific file."""
        service = self._get_service()
        return service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, createdTime, modifiedTime, size, webViewLink"
        ).execute()


def is_available() -> bool:
    """Check if Google Drive integration is available."""
    return GOOGLE_API_AVAILABLE

