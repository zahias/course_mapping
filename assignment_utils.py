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

def validate_assignments(edited_df, per_student_assignments):
    allowed = get_allowed_assignment_types()
    errors = []
    new_asgs = {}
    for _, row in edited_df.iterrows():
        sid = str(row['ID'])
        course = row['Course']
        if sid not in new_asgs:
            new_asgs[sid] = {}
        for atype in allowed:
            if row.get(atype, False):
                if atype in new_asgs[sid]:
                    errors.append(f"Student ID {sid} has multiple {atype} courses selected.")
                else:
                    new_asgs[sid][atype] = course
    for sid, assigns in new_asgs.items():
        if sid not in per_student_assignments:
            per_student_assignments[sid] = assigns
        else:
            per_student_assignments[sid].update(assigns)
    return errors, per_student_assignments

def save_assignments(assignments, db_path='assignments.db', csv_path='sce_fec_assignments.csv'):
    # save to sqlite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for sid, asg in assignments.items():
        for atype, course in asg.items():
            cursor.execute('''
                INSERT OR REPLACE INTO assignments (student_id, assignment_type, course)
                VALUES (?, ?, ?)
            ''', (sid, atype, course))
    conn.commit()
    conn.close()
    # save to csv
    rows = []
    for sid, asg in assignments.items():
        for atype, course in asg.items():
            rows.append({'student_id': sid, 'assignment_type': atype, 'course': course})
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    # sync to GDrive
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        fid = search_file(service, csv_path)
        if fid:
            update_file(service, fid, csv_path)
            st.info("Assignments file updated on Google Drive.")
        else:
            upload_file(service, csv_path, csv_path)
            st.info("Assignments file uploaded to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing assignments with Google Drive: {e}")

def reset_assignments(csv_path='sce_fec_assignments.csv', db_path='assignments.db'):
    if os.path.exists(csv_path):
        os.remove(csv_path)
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        fid = search_file(service, csv_path)
        if fid:
            delete_file(service, fid)
    except Exception as e:
        st.error(f"Error resetting assignments on Google Drive: {e}")
    if os.path.exists(db_path):
        os.remove(db_path)
