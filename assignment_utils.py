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

def save_assignments(assignments, db_path='assignments.db', csv_path='sce_fec_assignments.csv'):
    # Save to SQLite database
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
    # Save to local CSV file
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
    # Sync to Google Drive: if file exists, update; else, upload new
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        folder_id = None  # Modify if you use a specific folder.
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
    if os.path.exists(db_path):
        os.remove(db_path)
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, csv_path)
        if file_id:
            delete_file(service, file_id)
    except Exception as e:
        st.error(f"Error resetting assignments on Google Drive: {e}")
