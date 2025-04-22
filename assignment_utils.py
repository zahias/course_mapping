<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import sqlite3
=======
>>>>>>> parent of abfac76 (3)
=======
>>>>>>> parent of abfac76 (3)
import os
import pandas as pd
import pandas.errors
import streamlit as st
<<<<<<< HEAD
from config import get_allowed_assignment_types
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of abfac76 (3)
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    download_file,
=======
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
>>>>>>> parent of a8b67f1 (4)
    update_file,
    upload_file,
    delete_file
)
<<<<<<< HEAD
<<<<<<< HEAD
=======
from google_drive_utils import authenticate_google_drive, search_file, update_file, upload_file, delete_file
>>>>>>> parent of 98d5b2a (3)
=======
>>>>>>> parent of abfac76 (3)
=======
from google_drive_utils import authenticate_google_drive, search_file, download_file, update_file, upload_file, delete_file
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
=======
>>>>>>> parent of a8b67f1 (4)
from googleapiclient.discovery import build

CSV_PATH = 'sce_fec_assignments.csv'

<<<<<<< HEAD
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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
def load_assignments(csv_path: str = CSV_PATH, db_path: str = DB_PATH):
=======
def load_assignments(file_path: str = CSV_PATH):
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
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
<<<<<<< HEAD
    allowed = get_allowed_assignment_types()
=======
def save_assignment(conn, student_id, course_code, assignment_type):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
            VALUES (?, ?, ?)
        ''', (student_id, assignment_type, course_code))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving assignment: {e}")

def delete_assignment(conn, student_id, assignment_type):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            DELETE FROM assignments WHERE student_id = ? AND assignment_type = ?
        ''', (student_id, assignment_type))
        conn.commit()
    except Exception as e:
        st.error(f"Error deleting assignment: {e}")

=======
>>>>>>> parent of a8b67f1 (4)
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
<<<<<<< HEAD
=======
def load_assignments(csv_path: str = CSV_PATH, db_path: str = DB_PATH):
>>>>>>> parent of abfac76 (3)
    """
    Load assignments from Google Drive (CSV) and SQLite DB.
    If the CSV is empty or missing, returns {}.
    """
<<<<<<< HEAD
    allowed_assignment_types = get_allowed_assignment_types()
>>>>>>> parent of 98d5b2a (3)
=======
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
>>>>>>> parent of abfac76 (3)
=======
    allowed = get_allowed_assignment_types()
>>>>>>> parent of a8b67f1 (4)
    errors = []
    new = {}

    for _, row in edited_df.iterrows():
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of abfac76 (3)
        sid = str(row.get('ID','')).strip()
        course = row.get('Course','')
        if not sid or not course:
            continue
        new_assignments.setdefault(sid, {})
        for atype in allowed:
<<<<<<< HEAD
            if row.get(atype, False):
                if atype in new_assignments[sid]:
                    errors.append(f"Student {sid} has multiple {atype} selected.")
                else:
                    new_assignments[sid][atype] = course

    # Merge into existing
=======
        student_id = str(row['ID'])
        course = row['Course']
        if student_id not in new_assignments:
            new_assignments[student_id] = {}
        for atype in allowed_assignment_types:
=======
>>>>>>> parent of abfac76 (3)
            if row.get(atype, False):
                if atype in new_assignments[sid]:
                    errors.append(f"Student {sid} has multiple {atype} selected.")
                else:
                    new_assignments[sid][atype] = course

<<<<<<< HEAD
    # Merge into per_student_assignments
>>>>>>> parent of 98d5b2a (3)
=======
    # Merge into existing
>>>>>>> parent of abfac76 (3)
    for sid, assigns in new_assignments.items():
        if sid not in per_student_assignments:
            per_student_assignments[sid] = assigns
        else:
            per_student_assignments[sid].update(assigns)
=======
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
>>>>>>> parent of a8b67f1 (4)

    return errors, per_student_assignments

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of abfac76 (3)
def save_assignments(assignments: dict, csv_path: str = CSV_PATH):
    """
    Save assignments to CSV and sync to Google Drive.
    """
    # Save to CSV
    rows = []
    for sid, assigns in assignments.items():
        for atype, course in assigns.items():
            rows.append({
<<<<<<< HEAD
=======
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

<<<<<<< HEAD
    # Save to CSV and sync to Drive
    assignments_list = []
    for sid, assign in assignments.items():
        for atype, course in assign.items():
            assignments_list.append({
>>>>>>> parent of 98d5b2a (3)
=======
>>>>>>> parent of abfac76 (3)
                'student_id': sid,
                'assignment_type': atype,
                'course': course
            })
<<<<<<< HEAD
<<<<<<< HEAD
    df = pd.DataFrame(rows)
=======
    df = pd.DataFrame(assignments_list)
>>>>>>> parent of 98d5b2a (3)
=======
    df = pd.DataFrame(rows)
>>>>>>> parent of abfac76 (3)
=======
    # CSV + Drive sync
    df = pd.DataFrame([
        {'student_id':sid, 'assignment_type':atype, 'course':course}
        for sid, assigns in assignments.items()
        for atype, course in assigns.items()
    ])
>>>>>>> parent of a8b67f1 (4)
    df.to_csv(csv_path, index=False)

    # Sync to Drive
    try:
        creds = authenticate_google_drive()
<<<<<<< HEAD
        service = build('drive', 'v3', credentials=creds)
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of abfac76 (3)
        file_id = search_file(service, csv_path)
=======
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
>>>>>>> parent of a8b67f1 (4)
=======
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
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
        if file_id:
            update_file(service, file_id, file_path)
            st.info("Assignments updated on Google Drive.")
<<<<<<< HEAD
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments uploaded to Google Drive.")
=======
        fid = search_file(service, csv_path)
        if fid:
            update_file(service, fid, csv_path)
            st.info("Assignments file updated on Google Drive.")
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments file uploaded to Google Drive.")
>>>>>>> parent of 98d5b2a (3)
    except Exception as e:
        st.error(f"Error syncing assignments with Google Drive: {e}")

<<<<<<< HEAD
=======
        else:
            upload_file(service, file_path, file_path)
            st.info("Assignments uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments to Google Drive: {e}")

<<<<<<< HEAD
>>>>>>> parent of abfac76 (3)
def reset_assignments(csv_path: str = CSV_PATH, db_path: str = DB_PATH):
=======
def reset_assignments(file_path: str = CSV_PATH):
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
    """
    Deletes the assignments CSV locally and on Google Drive.
    """
<<<<<<< HEAD
    # Delete local CSV
<<<<<<< HEAD
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # Delete on Drive
=======
    if os.path.exists(file_path):
        os.remove(file_path)
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, file_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        st.error(f"Error resetting on Drive: {e}")
=======
=======
import sqlite3
>>>>>>> parent of b0f8265 (Update assignment_utils.py)
import os
import streamlit as st
import pandas as pd
from config import get_allowed_assignment_types
from google_drive_utils import authenticate_google_drive, search_file, update_file, upload_file, delete_file
from googleapiclient.discovery import build

def init_db(db_name='assignments.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Create the table without a check constraint for assignment_type to allow dynamic types.
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

def save_assignment(conn, student_id, course_code, assignment_type):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
            VALUES (?, ?, ?)
        ''', (student_id, assignment_type, course_code))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving assignment: {e}")

def delete_assignment(conn, student_id, assignment_type):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            DELETE FROM assignments WHERE student_id = ? AND assignment_type = ?
        ''', (student_id, assignment_type))
        conn.commit()
    except Exception as e:
        st.error(f"Error deleting assignment: {e}")

def load_assignments(db_path='assignments.db'):
    # Ensure the assignments table exists before querying
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, course, assignment_type FROM assignments')
    rows = cursor.fetchall()
    conn.close()

    assignments = {}
    for student_id, course_code, assignment_type in rows:
        if student_id not in assignments:
            assignments[student_id] = {}
        assignments[student_id][assignment_type] = course_code
    return assignments

def close_db(conn):
    conn.close()

def validate_assignments(edited_df, per_student_assignments):
    """
    Validates the assignments edited by the user.
    Checks that no student has multiple courses selected for the same assignment type.
    
    Returns:
      - errors: A list of error messages.
      - per_student_assignments: The updated assignments dictionary.
    """
    allowed_assignment_types = get_allowed_assignment_types()
    errors = []
    new_assignments = {}

    for _, row in edited_df.iterrows():
        student_id = str(row['ID'])
        course = row['Course']
        if student_id not in new_assignments:
            new_assignments[student_id] = {}
        for assign_type in allowed_assignment_types:
            if row.get(assign_type, False):
                if assign_type in new_assignments[student_id]:
                    errors.append(f"Student ID {student_id} has multiple {assign_type} courses selected.")
                else:
                    new_assignments[student_id][assign_type] = course

    for student_id, assignments in new_assignments.items():
        if student_id not in per_student_assignments:
            per_student_assignments[student_id] = assignments
        else:
            per_student_assignments[student_id].update(assignments)

    return errors, per_student_assignments

def save_assignments(assignments, db_path='assignments.db', csv_path='sce_fec_assignments.csv'):
    # Save to the SQLite database.
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for student_id, assignment in assignments.items():
        for assignment_type, course in assignment.items():
            cursor.execute('''
                INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
                VALUES (?, ?, ?)
            ''', (student_id, assignment_type, course))
    conn.commit()
    conn.close()

    # Also save assignments to a CSV file for Google Drive syncing.
    assignments_list = []
    for student_id, assignment in assignments.items():
        for assignment_type, course in assignment.items():
            assignments_list.append({
                'student_id': student_id,
                'assignment_type': assignment_type,
                'course': course
            })
    assignments_df = pd.DataFrame(assignments_list)
    assignments_df.to_csv(csv_path, index=False)

    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        folder_id = None  # Adjust if you need to use a specific folder.
        file_id = search_file(service, csv_path, folder_id=folder_id)
        if file_id:
            update_file(service, file_id, csv_path)
            st.info("Assignments file updated on Google Drive.")
        else:
            upload_file(service, csv_path, csv_path, folder_id=folder_id)
            st.info("Assignments file uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments with Google Drive: {e}")

def reset_assignments(csv_path='sce_fec_assignments.csv', db_path='assignments.db'):
    if os.path.exists(csv_path):
        os.remove(csv_path)
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
<<<<<<< HEAD
        st.error(f"Error deleting assignments on Google Drive: {e}")
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
<<<<<<< HEAD
=======
        st.error(f"Error resetting assignments on Drive: {e}")
>>>>>>> parent of 98d5b2a (3)
=======
        st.error(f"Error deleting assignments from Google Drive: {e}")

    # Remove and reinitialize local DB
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
>>>>>>> parent of abfac76 (3)
=======
def reset_assignments(csv_path='sce_fec_assignments.csv', db_path='assignments.db'):
    # Local cleanup
=======
>>>>>>> parent of abfac76 (3)
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
<<<<<<< HEAD
        st.error(f"Error resetting assignments on Drive: {e}")
>>>>>>> parent of 98d5b2a (3)
=======
        st.error(f"Error deleting assignments from Google Drive: {e}")

    # Remove and reinitialize local DB
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
>>>>>>> parent of abfac76 (3)
=======
        st.error(f"Error deleting assignments on Google Drive: {e}")
>>>>>>> parent of 04325c3 (Update assignment_utils.py)
=======
        st.error(f"Error resetting assignments on Google Drive: {e}")

    if os.path.exists(db_path):
        os.remove(db_path)
>>>>>>> parent of b0f8265 (Update assignment_utils.py)
=======
>>>>>>> parent of a8b67f1 (4)
