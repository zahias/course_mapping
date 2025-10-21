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

def _active_assignment_types():
    """
    Resolve the current assignment type list with per-Major override if present.
    """
    major = st.session_state.get("selected_major")
    if major:
        override = st.session_state.get(f"{major}_allowed_assignment_types")
        if isinstance(override, (list, tuple)) and len(override) > 0:
            return [str(x) for x in override if str(x).strip()]
    # Fallback to global/default
    return [str(x) for x in get_allowed_assignment_types()]

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
    # 1) Try to read from CSV first
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

    # 2) Fallback to SQLite DB
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

def validate_assignments(edited_df: pd.DataFrame, existing_assignments: dict):
    """
    Validates and produces an UPDATED assignments mapping that supports:
      - adding new assignments (checked boxes)
      - removing assignments (unchecked boxes)

    Returns:
      - errors: list[str]
      - updated_assignments: dict
    """
    allowed_assignment_types = _active_assignment_types()
    errors = []

    # Only consider types that exist as columns (freshly changed lists won't crash)
    present_types = [t for t in allowed_assignment_types if t in edited_df.columns]

    # Build the *selected* map from the edited grid
    selected: dict[str, dict[str, str]] = {}
    for _, row in edited_df.iterrows():
        sid = str(row.get("ID", "")).strip()
        crs = str(row.get("Course", "")).strip()
        if not sid or not crs:
            continue
        for at in present_types:
            if bool(row.get(at, False)):
                # Each slot can only hold one course per student
                if sid not in selected:
                    selected[sid] = {}
                if at in selected[sid] and selected[sid][at] != crs:
                    errors.append(f"Student {sid}: slot '{at}' already chosen for {selected[sid][at]} (cannot also choose {crs}).")
                else:
                    selected.setdefault(sid, {})[at] = crs

    # Start from a copy of current assignments
    updated = {sid: mapping.copy() for sid, mapping in existing_assignments.items()}

    # 1) Remove unselected slots (support unassign)
    for sid, mapping in list(updated.items()):
        for at in list(mapping.keys()):
            if at == "_note":
                continue
            # If this atype isn't selected now, remove it
            if sid not in selected or at not in selected[sid]:
                del updated[sid][at]
        # Clean up empty dicts except note
        if not any(k != "_note" for k in updated[sid].keys()):
            # keep the note if present
            if "_note" in updated[sid] and updated[sid]["_note"]:
                updated[sid] = {"_note": updated[sid]["_note"]}
            else:
                del updated[sid]

    # 2) Add/overwrite selected slots
    for sid, slots in selected.items():
        for at, crs in slots.items():
            updated.setdefault(sid, {})[at] = crs

    return errors, updated

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
    # Clear table to exactly mirror the in-memory mapping
    cursor.execute('DELETE FROM assignments')
    for student_id, assign_map in assignments.items():
        for assignment_type, course in assign_map.items():
            if assignment_type == "_note":
                continue
            cursor.execute('''
                INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
                VALUES (?, ?, ?)
            ''', (student_id, assignment_type, course))
    conn.commit()
    conn.close()

    # --- 2) Persist to CSV for Google Drive syncing ---
    rows = []
    for student_id, assign_map in assignments.items():
        for assignment_type, course in assign_map.items():
            if assignment_type == "_note":
                continue
            rows.append({
                "student_id": student_id,
                "assignment_type": assignment_type,
                "course": course
            })
    pd.DataFrame(rows).to_csv(csv_path, index=False)

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
    Completely clears all assignments for this major:
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
