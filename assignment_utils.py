import sqlite3
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
    # Remove the local CSV file.
    if os.path.exists(csv_path):
        os.remove(csv_path)

    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
        st.error(f"Error resetting assignments on Google Drive: {e}")

    # Also remove the local SQLite database file.
    if os.path.exists(db_path):
        os.remove(db_path)
