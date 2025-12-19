import io
import os
import streamlit as st
import time
from functools import wraps
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def authenticate_google_drive():
    client_id = None
    client_secret = None
    refresh_token = None
    token_uri = "https://oauth2.googleapis.com/token"

    if os.environ.get("GOOGLE_CLIENT_ID"):
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
        token_uri = os.environ.get("GOOGLE_TOKEN_URI", token_uri)
    elif "google" in st.secrets:
        client_id = st.secrets["google"]["client_id"]
        client_secret = st.secrets["google"]["client_secret"]
        refresh_token = st.secrets["google"]["refresh_token"]
        token_uri = st.secrets["google"].get("token_uri", token_uri)

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing Google Drive credentials. Please set up credentials in Secrets.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    creds.refresh(Request())

    return creds

def upload_file(service, file_path, file_name, folder_id=None):
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def update_file(service, file_id, file_path):
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().update(fileId=file_id, media_body=media).execute()
    return file.get('id')

def download_file(service, file_id, file_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.close()

def search_file(service, file_name, folder_id=None):
    query = f"name='{file_name}' and trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    else:
        return None

def delete_file(service, file_id):
    service.files().delete(fileId=file_id).execute()


def retry_on_error(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Decorator to retry Google Drive operations on failure.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    last_error = e
                    error_code = e.resp.status if hasattr(e, 'resp') else None
                    
                    # Don't retry on authentication errors or not found errors
                    if error_code in [401, 403, 404]:
                        raise
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


def handle_drive_error(func):
    """
    Decorator to provide user-friendly error messages for Google Drive operations.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            error_code = e.resp.status if hasattr(e, 'resp') else None
            error_reason = e.error_details[0].get('reason', '') if hasattr(e, 'error_details') and e.error_details else ''
            
            if error_code == 401:
                st.error("**Authentication Error:** Google Drive credentials are invalid or expired. Please check your credentials.")
            elif error_code == 403:
                st.error("**Permission Denied:** You don't have permission to access this file. Please check file permissions.")
            elif error_code == 404:
                st.error("**File Not Found:** The requested file was not found on Google Drive.")
            elif error_code == 429:
                st.error("**Rate Limit Exceeded:** Too many requests to Google Drive. Please wait a moment and try again.")
            elif error_code >= 500:
                st.error(f"**Google Drive Service Error:** Google Drive is experiencing issues (Error {error_code}). Please try again later.")
            else:
                st.error(f"**Google Drive Error:** {str(e)}")
            raise
        except ValueError as e:
            if "credentials" in str(e).lower():
                st.error("**Configuration Error:** Google Drive credentials are not properly configured. Please check your settings.")
            else:
                st.error(f"**Error:** {str(e)}")
            raise
        except Exception as e:
            st.error(f"**Unexpected Error:** {str(e)}")
            raise
    return wrapper


# Apply error handling to key functions
@handle_drive_error
@retry_on_error()
def upload_file_safe(service, file_path, file_name, folder_id=None):
    """Upload file with error handling and retry logic."""
    return upload_file(service, file_path, file_name, folder_id)


@handle_drive_error
@retry_on_error()
def update_file_safe(service, file_id, file_path):
    """Update file with error handling and retry logic."""
    return update_file(service, file_id, file_path)


@handle_drive_error
@retry_on_error()
def download_file_safe(service, file_id, file_path):
    """Download file with error handling and retry logic."""
    return download_file(service, file_id, file_path)


@handle_drive_error
@retry_on_error()
def search_file_safe(service, file_name, folder_id=None):
    """Search file with error handling and retry logic."""
    return search_file(service, file_name, folder_id)
