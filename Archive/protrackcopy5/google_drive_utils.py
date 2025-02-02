import os
import io
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    try:
        client_id = st.secrets["google"]["client_id"]
        client_secret = st.secrets["google"]["client_secret"]
        refresh_token = st.secrets["google"]["refresh_token"]
        token_uri = st.secrets["google"].get("token_uri", "https://oauth2.googleapis.com/token")
    except Exception as e:
        st.error(
            "Google credentials not found in st.secrets. "
            "Please create a secrets.toml file in one of the following paths:\n"
            "  - /Users/zahi/.streamlit/secrets.toml\n"
            "  - /Users/zahi/ProTrack/.streamlit/secrets.toml\n\n"
            "The file should contain your Google OAuth2 credentials in the following format:\n\n"
            "[google]\n"
            "client_id = \"YOUR_GOOGLE_CLIENT_ID\"\n"
            "client_secret = \"YOUR_GOOGLE_CLIENT_SECRET\"\n"
            "refresh_token = \"YOUR_REFRESH_TOKEN\"\n"
            "token_uri = \"https://oauth2.googleapis.com/token\"\n"
        )
        raise e

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    # Refresh credentials if needed
    if creds and creds.expired and creds.refresh_token:
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
