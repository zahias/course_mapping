import os
import pandas as pd
import streamlit as st
from google_drive_utils import authenticate_google_drive, search_file, download_file, update_file, upload_file, delete_file
from googleapiclient.discovery import build

def load_assignments(file_path='sce_fec_assignments.csv'):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    file_id = search_file(service, file_path)
    if file_id:
        download_file(service, file_id, file_path)
        try:
            assignments_df = pd.read_csv(file_path)
            if assignments_df.empty:
                st.warning("Assignments file is empty.")
                return {}
        except pd.errors.EmptyDataError:
            st.warning("Assignments file is empty or invalid.")
            return {}
        except Exception as e:
            st.error(f"Error reading assignments file: {e}")
            return {}
        per_student_assignments = {}
        for _, row in assignments_df.iterrows():
            student_id = str(row['student_id'])
            assignment_type = row['assignment_type']
            course = row['course']
            if student_id not in per_student_assignments:
                per_student_assignments[student_id] = {}
            per_student_assignments[student_id][assignment_type] = course
        return per_student_assignments
    else:
        return {}

def save_assignments(per_student_assignments, file_path='sce_fec_assignments.csv'):
    assignments_list = []
    for student_id, assignments in per_student_assignments.items():
        for assignment_type, course in assignments.items():
            assignments_list.append({'student_id': student_id, 'assignment_type': assignment_type, 'course': course})
    assignments_df = pd.DataFrame(assignments_list)
    assignments_df.to_csv(file_path, index=False)

    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    folder_id = None
    file_id = search_file(service, file_path, folder_id=folder_id)
    if file_id:
        update_file(service, file_id, file_path)
        st.info("Assignments file updated on Google Drive.")
    else:
        upload_file(service, file_path, file_path, folder_id=folder_id)
        st.info("Assignments file uploaded to Google Drive.")

def reset_assignments(file_path='sce_fec_assignments.csv'):
    if os.path.exists(file_path):
        os.remove(file_path)

    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    file_id = search_file(service, file_path)
    if file_id:
        delete_file(service, file_id)

def validate_assignments(edited_df, per_student_assignments):
    errors = []
    new_assignments = {}

    for _, row in edited_df.iterrows():
        student_id = str(row['ID'])
        sce_selected = row['S.C.E.']
        fec_selected = row['F.E.C.']
        course = row['Course']

        if student_id not in new_assignments:
            new_assignments[student_id] = {}

        if sce_selected and fec_selected:
            errors.append(f"Course {course} for Student ID {student_id} cannot be both S.C.E. and F.E.C.")
            continue

        if sce_selected:
            if 'S.C.E.' in new_assignments[student_id]:
                errors.append(f"Student ID {student_id} has multiple S.C.E. courses selected.")
            else:
                new_assignments[student_id]['S.C.E.'] = course
        if fec_selected:
            if 'F.E.C.' in new_assignments[student_id]:
                errors.append(f"Student ID {student_id} has multiple F.E.C. courses selected.")
            else:
                new_assignments[student_id]['F.E.C.'] = course

    for student_id, assignments in new_assignments.items():
        if student_id not in per_student_assignments:
            per_student_assignments[student_id] = assignments
        else:
            per_student_assignments[student_id].update(assignments)

    return errors, per_student_assignments
