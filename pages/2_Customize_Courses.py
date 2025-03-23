import streamlit as st
import pandas as pd
from config import get_default_target_courses, get_intensive_courses
from google_drive_utils import authenticate_google_drive, search_file, download_file, upload_file, update_file
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define required and intensive courses. The CSV should contain "
    "'Course', 'Credits', and optionally 'Type' (Required or Intensive) and 'Passing Grades' (comma separated). "
    "If 'Type' is not provided, all courses are considered Required and default intensive courses are used."
)

# Define the file name to sync on Google Drive
custom_courses_file_name = "custom_courses.csv"

# First, if no file is uploaded in this session, try to load from Google Drive
uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)", type="csv", help="Use the template below.")
if uploaded_courses is None:
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, custom_courses_file_name)
        if file_id:
            download_file(service, file_id, custom_courses_file_name)
            st.info("Loaded custom courses file from Google Drive.")
            uploaded_courses = open(custom_courses_file_name, "rb")
    except Exception as e:
        st.error(f"Error loading custom courses from Google Drive: {e}")

if st.button("Download Template", help="Download a CSV template to define courses and custom passing grades."):
    template_df = pd.DataFrame({
        'Course': ['ENGL201', 'CHEM201', 'INEG200', 'MATH101', 'ACCT201'],
        'Credits': [3, 3, 3, 3, 3],
        'Type': ['Required', 'Required', 'Intensive', 'Required', 'Required'],
        'Passing Grades': ['A,A-,B+,B', '', 'A,A-,B+,B', 'A,A-,B+,B,C+', 'A,A-,B+,B,C+,C,C-']  # For ACCT201, note: D, D-, D+ are omitted
    })
    csv_data = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV Template",
        data=csv_data,
        file_name='course_template.csv',
        mime='text/csv'
    )

if 'raw_df' not in st.session_state:
    st.warning("No data uploaded yet. Please upload data first in 'Upload Data' page.")
else:
    if uploaded_courses is not None:
        try:
            custom_df = pd.read_csv(uploaded_courses)
            if 'Course' in custom_df.columns and 'Credits' in custom_df.columns:
                if 'Type' in custom_df.columns:
                    required_df = custom_df[custom_df['Type'].str.lower() == 'required']
                    intensive_df = custom_df[custom_df['Type'].str.lower() == 'intensive']
                    st.session_state['target_courses'] = dict(zip(required_df['Course'].str.upper(), required_df['Credits']))
                    st.session_state['intensive_courses'] = dict(zip(intensive_df['Course'].str.upper(), intensive_df['Credits']))
                else:
                    st.session_state['target_courses'] = dict(zip(custom_df['Course'].str.upper(), custom_df['Credits']))
                    st.session_state['intensive_courses'] = get_intensive_courses()
                
                # Build a mapping for custom passing grades (normalize course codes to uppercase)
                custom_passing = {}
                if 'Passing Grades' in custom_df.columns:
                    for _, row in custom_df.iterrows():
                        course = row['Course'].strip().upper()
                        passing = row.get('Passing Grades', '')
                        if pd.notna(passing) and passing != '':
                            custom_passing[course] = [grade.strip() for grade in passing.split(',') if grade.strip()]
                st.session_state['custom_passing_grades'] = custom_passing
                
                st.success("Custom courses (and custom passing grades) loaded from CSV.")
                
                # Sync the custom courses file to Google Drive
                try:
                    creds = authenticate_google_drive()
                    service = build('drive', 'v3', credentials=creds)
                    folder_id = None  # Change if you need a specific folder
                    # Save local file
                    custom_df.to_csv(custom_courses_file_name, index=False)
                    file_id = search_file(service, custom_courses_file_name, folder_id=folder_id)
                    if file_id:
                        update_file(service, file_id, custom_courses_file_name)
                        st.info("Custom courses file updated on Google Drive.")
                    else:
                        upload_file(service, custom_courses_file_name, custom_courses_file_name, folder_id=folder_id)
                        st.info("Custom courses file uploaded to Google Drive.")
                except Exception as e:
                    st.error(f"Error syncing custom courses file to Google Drive: {e}")
            else:
                st.error("CSV must contain 'Course' and 'Credits' columns.")
        except Exception as e:
            st.error(f"Error reading custom courses file: {e}")
    else:
        st.session_state['target_courses'] = get_default_target_courses()
        st.session_state['intensive_courses'] = get_intensive_courses()
        st.info("Using default required and intensive courses.")

    st.success("Courses are now set. Proceed to 'View Reports' to see the processed data.")

    with st.expander("Assignment Types Configuration", expanded=True):
        st.write("Edit the list of assignment types that can be assigned to courses. For example, enter S.C.E, F.E.C, ARAB201 to allow assignments for those courses.")
        default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
        assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
        if st.button("Save Assignment Types"):
            new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
            st.session_state["allowed_assignment_types"] = new_types
            st.success("Assignment types updated.")
