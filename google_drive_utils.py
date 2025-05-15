import io
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    # Build credentials from st.secrets. We assume the user has added:
    # [google]
    # client_id = "YOUR_GOOGLE_CLIENT_ID"
    # client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
    # refresh_token = "YOUR_REFRESH_TOKEN"
    # token_uri = "https://oauth2.googleapis.com/token"
    client_id     = st.secrets["google"]["client_id"]
    client_secret = st.secrets["google"]["client_secret"]
    refresh_token = st.secrets["google"]["refresh_token"]
    token_uri     = st.secrets["google"].get("token_uri", "https://oauth2.googleapis.com/token")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    # Refresh if needed
    from google.auth.transport.requests import Request
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds

def upload_file(service, file_path, file_name, folder_id=None):
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata, media_body=media, fields='id'
    ).execute()
    return file.get('id')

def update_file(service, file_id, file_path):
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().update(
        fileId=file_id, media_body=media
    ).execute()
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
        q=query, spaces='drive', fields='files(id, name)', pageSize=1
    ).execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    else:
        return None

def delete_file(service, file_id):
    service.files().delete(fileId=file_id).execute()


# ─────────── New Helpers ───────────

def sync_to_drive(local_path: str, drive_name: str, folder_id: str = None):
    """
    Uploads or updates a local file to Google Drive under the given drive_name.
    If a file with that name already exists (in the optional folder), it is updated.
    Otherwise, it is created.
    """
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    existing_id = search_file(service, drive_name, folder_id)
    if existing_id:
        update_file(service, existing_id, local_path)
    else:
        upload_file(service, local_path, drive_name, folder_id)

def reload_from_drive(drive_name: str, local_path: str, folder_id: str = None) -> bool:
    """
    Downloads a file named drive_name from Google Drive (optional folder) to local_path.
    Returns True if the file was found & downloaded, False if not found.
    """
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    file_id = search_file(service, drive_name, folder_id)
    if not file_id:
        return False
    download_file(service, file_id, local_path)
    return True
