<<<<<<< HEAD
import sqlite3
import os
import streamlit as st
import pandas as pd
from config import get_allowed_assignment_types
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    update_file,
    upload_file,
    delete_file
)
from googleapiclient.discovery import build

def init_db(db_name='assignments.db'):
    conn = sqlite3.connect(db_name)
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

def load_assignments(db_path='assignments.db'):
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, course, assignment_type FROM assignments')
    rows = cursor.fetchall()
    conn.close()
    per = {}
    for sid, course, atype in rows:
        per.setdefault(sid, {})[atype] = course
    return per

def validate_assignments(edited_df, per_student_assignments):
    allowed = get_allowed_assignment_types()
    errors = []
    new = {}

    for _, row in edited_df.iterrows():
        sid = str(row['ID'])
        crs = row['Course']
        new.setdefault(sid, {})
        for at in allowed:
            if row.get(at, False):
                if at in new[sid]:
                    errors.append(f"Student {sid} has multiple {at}")
                else:
                    new[sid][at] = crs

    # Merge
    for sid, assigns in new.items():
        per_student_assignments.setdefault(sid, {}).update(assigns)

    return errors, per_student_assignments

def save_assignments(assignments, db_path='assignments.db', csv_path='sce_fec_assignments.csv'):
    # SQLite
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for sid, assigns in assignments.items():
        for atype, course in assigns.items():
            cur.execute('''
                INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
                VALUES (?, ?, ?)
            ''', (sid, atype, course))
    conn.commit()
    conn.close()

    # CSV + Drive sync
    df = pd.DataFrame([
        {'student_id':sid, 'assignment_type':atype, 'course':course}
        for sid, assigns in assignments.items()
        for atype, course in assigns.items()
    ])
    df.to_csv(csv_path, index=False)

    try:
        creds = authenticate_google_drive()
        service = build('drive','v3',credentials=creds)
        fid = search_file(service, csv_path)
        if fid:
            update_file(service, fid, csv_path)
            st.info("Assignments synced to Drive.")
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments uploaded to Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments: {e}")

def reset_assignments(csv_path='sce_fec_assignments.csv', db_path='assignments.db'):
    if os.path.exists(csv_path):
        os.remove(csv_path)
    if os.path.exists(db_path):
        os.remove(db_path)
    try:
        creds = authenticate_google_drive()
        service = build('drive','v3',credentials=creds)
        fid = search_file(service, csv_path)
        if fid:
            delete_file(service, fid)
    except Exception as e:
        st.error(f"Error resetting on Drive: {e}")
=======
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
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
