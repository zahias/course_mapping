# utilities.py

import pandas as pd
import os
import streamlit as st
import sqlite3

def save_uploaded_file(uploaded_file, folder='uploads'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filepath = os.path.join(folder, uploaded_file.name)
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def load_csv(filepath):
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return None

def load_excel(filepath, sheet_name):
    try:
        return pd.read_excel(filepath, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return None

# New database utility functions

def init_db(db_name='assignments.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            assignment_type TEXT NOT NULL CHECK(assignment_type IN ('S.C.E.', 'F.E.C.')),
            UNIQUE(student_id, assignment_type)
        )
    ''')
    conn.commit()
    return conn

def save_assignment(conn, student_id, course_code, assignment_type):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assignments (student_id, course_code, assignment_type)
            VALUES (?, ?, ?)
        ''', (student_id, course_code, assignment_type))
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

def load_assignments(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, course_code, assignment_type FROM assignments')
    rows = cursor.fetchall()
    assignments = {}
    for student_id, course_code, assignment_type in rows:
        if student_id not in assignments:
            assignments[student_id] = {}
        assignments[student_id][assignment_type] = course_code
    return assignments

def close_db(conn):
    conn.close()
