"""Google Docs integration for extracting document text."""
import os
from typing import Dict, Any, Optional

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GoogleDocsClient:
    """Client for Google Docs operations."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/documents.readonly',
    ]
    
    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """Initialize with OAuth credentials."""
        self.credentials = credentials
        self._service = None
    
    def _get_service(self):
        """Get or create Docs API service."""
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
            self._service = build('docs', 'v1', credentials=creds)
        
        return self._service
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get full document data."""
        service = self._get_service()
        return service.documents().get(documentId=document_id).execute()
    
    def extract_text(self, document_id: str) -> str:
        """
        Extract plain text content from a Google Doc.
        
        Args:
            document_id: The ID of the Google Doc
            
        Returns:
            Plain text content of the document
        """
        doc = self.get_document(document_id)
        
        # Extract text from document body
        content = doc.get('body', {}).get('content', [])
        text_parts = []
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_parts.append(elem['textRun'].get('content', ''))
        
        return ''.join(text_parts)
    
    def get_document_title(self, document_id: str) -> str:
        """Get the title of a Google Doc."""
        doc = self.get_document(document_id)
        return doc.get('title', '')


def is_available() -> bool:
    """Check if Google Docs integration is available."""
    return GOOGLE_API_AVAILABLE

