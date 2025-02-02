# database_utils.py

import sqlite3
import os

def initialize_database(db_path='assignments.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            student_id TEXT,
            assignment_type TEXT,
            course TEXT,
            PRIMARY KEY (student_id, assignment_type)
        )
    ''')
    conn.commit()
    conn.close()

def load_assignments(db_path='assignments.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT student_id, assignment_type, course FROM assignments')
    rows = cursor.fetchall()
    conn.close()

    per_student_assignments = {}
    for student_id, assignment_type, course in rows:
        if student_id not in per_student_assignments:
            per_student_assignments[student_id] = {}
        per_student_assignments[student_id][assignment_type] = course
    return per_student_assignments

def save_assignments(assignments, db_path='assignments.db'):
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
