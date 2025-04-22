import os
import pandas as pd
import pandas.errors
import streamlit as st
from google_drive_utils import authenticate_google_drive, search_file, download_file, update_file, upload_file, delete_file
from googleapiclient.discovery import build

CSV_PATH = 'sce_fec_assignments.csv'

def load_assignments(file_path: str = CSV_PATH):
    """
    Loads per‑student S.C.E./F.E.C. assignments from Google Drive (or local cache).
    If the CSV is empty or missing, returns {}.
    """
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    file_id = search_file(service, file_path)
    if file_id:
        # download the latest
        download_file(service, file_id, file_path)
        # read it
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            # empty file → no assignments
            st.warning("Assignments file is empty; starting with no assignments.")
            return {}
        except Exception as e:
            st.error(f"Error reading assignments file: {e}")
            return {}
        # convert to dict
        per_student = {}
        for _, row in df.iterrows():
            sid = str(row.get('student_id') or row.get('ID') or '').strip()
            atype = row.get('assignment_type', '').strip()
            course = row.get('course', '').strip()
            if not sid or not atype or not course:
                continue
            per_student.setdefault(sid, {})[atype] = course
        return per_student
    else:
        # no file on Drive → start empty
        return {}

def save_assignments(assignments: dict, file_path: str = CSV_PATH):
    """
    Saves the assignments dict to local CSV and syncs to Google Drive.
    """
    # build DataFrame
    rows = []
    for sid, assigns in assignments.items():
        for atype, course in assigns.items():
            rows.append({'student_id': sid, 'assignment_type': atype, 'course': course})
    df = pd.DataFrame(rows)
    # save locally
    df.to_csv(file_path, index=False)
    # sync to Drive
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, file_path)
        if file_id:
            update_file(service, file_id, file_path)
            st.info("Assignments updated on Google Drive.")
        else:
            upload_file(service, file_path, file_path)
            st.info("Assignments uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments to Google Drive: {e}")

def reset_assignments(file_path: str = CSV_PATH):
    """
    Deletes the assignments CSV locally and on Google Drive.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, file_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
        st.error(f"Error deleting assignments on Google Drive: {e}")
