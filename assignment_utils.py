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

def init_db(db_name: str = "assignments.db"):
    """
    Initialize (or connect to) the SQLite database for assignments.
    """
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

def save_assignment(conn, student_id: str, course_code: str, assignment_type: str):
    """
    Insert (or replace) a single assignment row into the SQLite DB.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
            VALUES (?, ?, ?)
        ''', (student_id, assignment_type, course_code))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving assignment to DB: {e}")

def delete_assignment(conn, student_id: str, assignment_type: str):
    """
    Delete a single assignment from the SQLite DB.
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            DELETE FROM assignments WHERE student_id = ? AND assignment_type = ?
        ''', (student_id, assignment_type))
        conn.commit()
    except Exception as e:
        st.error(f"Error deleting assignment from DB: {e}")

def load_assignments(db_path: str = "assignments.db", csv_path: str = "sce_fec_assignments.csv"):
    """
    Load per-student assignments, preferring the CSV at `csv_path` if it exists,
    otherwise falling back to the SQLite database at `db_path`.

    Returns a dict:
        {
          "student_id_1": {"S.C.E.": "COURSEX", "F.E.C.": "COURSEY", ...},
          "student_id_2": {...},
           ...
        }
    """
    # 1) Try to read from the CSV file first
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            per_student = {}
            for _, row in df.iterrows():
                sid = str(row["student_id"])
                atype = row["assignment_type"]
                course = row["course"]
                if sid not in per_student:
                    per_student[sid] = {}
                per_student[sid][atype] = course
            return per_student
        except Exception as e:
            st.warning(f"Could not read assignments CSV '{csv_path}': {e}")

    # 2) If CSV is missing or invalid, fall back to SQLite DB
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
    """
    Close the SQLite connection.
    """
    conn.close()

def validate_assignments(edited_df: pd.DataFrame, per_student_assignments: dict):
    """
    Validates the DataFrame returned by st.data_editor (or similar).
    Ensures no student has more than one course per assignment type.

    Returns:
      - errors: a list of human-readable error messages
      - updated per_student_assignments dict
    """
    allowed_assignment_types = get_allowed_assignment_types()
    errors = []
    new_assignments = {}

    for _, row in edited_df.iterrows():
        student_id = str(row["ID"])
        course = row["Course"]
        if student_id not in new_assignments:
            new_assignments[student_id] = {}
        for assign_type in allowed_assignment_types:
            if row.get(assign_type, False):
                if assign_type in new_assignments[student_id]:
                    errors.append(f"Student ID {student_id} has multiple {assign_type} courses selected.")
                else:
                    new_assignments[student_id][assign_type] = course

    # Merge new_assignments into the existing per_student_assignments
    for student_id, assigns in new_assignments.items():
        if student_id not in per_student_assignments:
            per_student_assignments[student_id] = assigns
        else:
            per_student_assignments[student_id].update(assigns)

    return errors, per_student_assignments

def save_assignments(
    assignments: dict,
    db_path: str = "assignments.db",
    csv_path: str = "sce_fec_assignments.csv"
):
    """
    Persist `assignments` both to the local SQLite DB and to a CSV for Drive syncing.

    The `assignments` dict should look like:
      {
        "2016123456": {"S.C.E.": "CMPS202", "F.E.C.": "ENGL201"},
        "2017012345": {"S.C.E.": "PBHL201"},
         ...
      }
    """
    # --- 1) Persist to SQLite DB ---
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for student_id, assign_map in assignments.items():
        for assignment_type, course in assign_map.items():
            cursor.execute('''
                INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
                VALUES (?, ?, ?)
            ''', (student_id, assignment_type, course))
    conn.commit()
    conn.close()

    # --- 2) Persist to CSV for Google Drive syncing ---
    assignments_list = []
    for student_id, assign_map in assignments.items():
        for assignment_type, course in assign_map.items():
            assignments_list.append({
                "student_id": student_id,
                "assignment_type": assignment_type,
                "course": course
            })
    assignments_df = pd.DataFrame(assignments_list)
    assignments_df.to_csv(csv_path, index=False)

    # --- 3) Sync to Google Drive ---
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            update_file(service, file_id, csv_path)
            st.info("Assignments file updated on Google Drive.")
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments file uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments with Google Drive: {e}")

def reset_assignments(csv_path: str = "sce_fec_assignments.csv", db_path: str = "assignments.db"):
    """
    Completely clears all assignments:
      - Deletes the local CSV (if it exists)
      - Deletes the CSV on Google Drive (if present)
      - Deletes the local SQLite DB file (if present)
    """
    # 1) Remove local CSV
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # 2) Remove from Google Drive
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
        st.error(f"Error resetting assignments on Google Drive: {e}")

    # 3) Remove local DB
    if os.path.exists(db_path):
        os.remove(db_path)
