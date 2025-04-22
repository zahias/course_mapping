import os
import sqlite3
import pandas as pd
import pandas.errors
import streamlit as st
from config import get_allowed_assignment_types
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    download_file,
    update_file,
    upload_file,
    delete_file
)
from googleapiclient.discovery import build

CSV_PATH = 'sce_fec_assignments.csv'
DB_PATH = 'assignments.db'

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            student_id TEXT NOT NULL,
            assignment_type TEXT NOT NULL,
            course TEXT NOT NULL,
            PRIMARY KEY (student_id, assignment_type)
        )
    ''')
    conn.commit()
    return conn

def load_assignments(csv_path: str = CSV_PATH, db_path: str = DB_PATH):
    """
    Load assignments from Google Drive (CSV) and SQLite DB.
    If the CSV is empty or missing, returns {}.
    """
    # Ensure local DB exists
    init_db(db_path)

    # First, try to sync down the CSV from Drive
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            download_file(service, file_id, csv_path)
    except Exception:
        # If Drive fails, proceed with whatever is local
        pass

    # Load from CSV
    per_student = {}
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            st.warning("Assignments file is empty; starting with no assignments.")
            return {}
        except Exception as e:
            st.error(f"Error reading assignments CSV: {e}")
            return {}
        for _, row in df.iterrows():
            sid = str(row.get('student_id','')).strip()
            atype = row.get('assignment_type','').strip()
            course = row.get('course','').strip()
            if sid and atype and course:
                per_student.setdefault(sid, {})[atype] = course
    return per_student

def validate_assignments(edited_df: pd.DataFrame, per_student_assignments: dict):
    """
    Validates that each student has at most one course per assignment type.
    Returns (errors, updated_dict).
    """
    allowed = get_allowed_assignment_types()
    errors = []
    new_assignments = {}

    for _, row in edited_df.iterrows():
        sid = str(row.get('ID','')).strip()
        course = row.get('Course','')
        if not sid or not course:
            continue
        new_assignments.setdefault(sid, {})
        for atype in allowed:
            if row.get(atype, False):
                if atype in new_assignments[sid]:
                    errors.append(f"Student {sid} has multiple {atype} selected.")
                else:
                    new_assignments[sid][atype] = course

    # Merge into existing
    for sid, assigns in new_assignments.items():
        if sid not in per_student_assignments:
            per_student_assignments[sid] = assigns
        else:
            per_student_assignments[sid].update(assigns)

    return errors, per_student_assignments

def save_assignments(assignments: dict, csv_path: str = CSV_PATH):
    """
    Save assignments to CSV and sync to Google Drive.
    """
    # Save to CSV
    rows = []
    for sid, assigns in assignments.items():
        for atype, course in assigns.items():
            rows.append({
                'student_id': sid,
                'assignment_type': atype,
                'course': course
            })
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    # Sync to Drive
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            update_file(service, file_id, csv_path)
            st.info("Assignments updated on Google Drive.")
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments with Google Drive: {e}")

def reset_assignments(csv_path: str = CSV_PATH, db_path: str = DB_PATH):
    """
    Deletes local CSV, deletes from Google Drive, and resets DB.
    """
    # Delete local CSV
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # Delete on Drive
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
        st.error(f"Error deleting assignments from Google Drive: {e}")

    # Remove and reinitialize local DB
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
