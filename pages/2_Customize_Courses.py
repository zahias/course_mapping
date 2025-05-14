import streamlit as st
import pandas as pd
import os
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    update_file,
    upload_file,
    download_file
)
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define courses configuration. The CSV must contain: "
    "`Course`, `Credits`, `PassingGrades`, `Type`, `FromSemester`, and `ToSemester`. "
    "The `PassingGrades` column is a comma-separated list of acceptable passing grades "
    "for that course in the specified range."
)

# --- Courses Configuration Section ---
with st.expander("Course Configuration Options", expanded=True):
    uploaded_courses = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="Use the template below."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template", help="Download the CSV template for courses configuration."):
            template_df = pd.DataFrame({
                'Course': ['ACCT201', 'ACCT201'],
                'Credits': [3, 3],
                'PassingGrades': ['C+,C,C-', 'A+,A,A-'],
                'Type': ['Required', 'Required'],
                'FromSemester': ['FALL-2016', 'SPRING-2018'],
                'ToSemester': ['SPRING-2018', 'FALL-2025']
            })
            csv_data = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Courses Template",
                data=csv_data,
                file_name='courses_template.csv',
                mime='text/csv'
            )
    with col2:
        if st.button("Reload Courses Configuration from Google Drive", help="Load courses configuration from Google Drive."):
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    download_file(service, file_id, "courses_config.csv")
                    st.success("Courses configuration reloaded from Google Drive.")
                else:
                    st.error("Courses configuration file not found on Google Drive.")
            except Exception as e:
                st.error(f"Error reloading courses configuration: {e}")

    # Load the CSV (either freshly uploaded or existing local copy)
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
            # Save locally
            courses_df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                folder_id = None
                file_id = search_file(service, "courses_config.csv", folder_id=folder_id)
                if file_id:
                    update_file(service, file_id, "courses_config.csv")
                else:
                    upload_file(service, "courses_config.csv", "courses_config.csv", folder_id=folder_id)
                st.info("Courses configuration synced to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing courses configuration: {e}")
        except Exception as e:
            st.error(f"Error reading the uploaded file: {e}")
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    if courses_df is not None:
        required_cols = {
            'Course',
            'Credits',
            'PassingGrades',
            'Type',
            'FromSemester',
            'ToSemester'
        }
        if not required_cols.issubset(courses_df.columns):
            st.error(f"CSV must contain columns: {required_cols}")
        else:
            # Normalize
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            # Separate by Type
            required_df = courses_df[courses_df['Type'].str.lower() == 'required']
            intensive_df = courses_df[courses_df['Type'].str.lower() == 'intensive']

            # Build term-range rules for each course
            target_rules = {}
            for _, row in required_df.iterrows():
                course = row['Course']
                rule = {
                    "Credits": int(row['Credits']),
                    "PassingGrades": row['PassingGrades'],
                    "FromSemester": row['FromSemester'].upper(),
                    "ToSemester": row['ToSemester'].upper()
                }
                target_rules.setdefault(course, []).append(rule)

            intensive_rules = {}
            for _, row in intensive_df.iterrows():
                course = row['Course']
                rule = {
                    "Credits": int(row['Credits']),
                    "PassingGrades": row['PassingGrades'],
                    "FromSemester": row['FromSemester'].upper(),
                    "ToSemester": row['ToSemester'].upper()
                }
                intensive_rules.setdefault(course, []).append(rule)

            # Store in session for processing
            st.session_state['target_rules'] = target_rules
            st.session_state['intensive_rules'] = intensive_rules

            st.success("Courses configuration loaded successfully.")

            # Optional: show loaded rules
            st.markdown("**Loaded Course Rules:**")
            st.json({
                "Required": target_rules,
                "Intensive": intensive_rules
            }, expanded=False)
    else:
        st.info("No courses configuration available. Please upload a file.")

# --- Equivalent Courses Section (unchanged) ---
with st.expander("Equivalent Courses", expanded=True):
    st.write("This section automatically loads the 'equivalent_courses.csv' file from Google Drive.")
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, "equivalent_courses.csv")
        if file_id:
            download_file(service, file_id, "equivalent_courses.csv")
            st.success("Equivalent courses file loaded from Google Drive.")
        else:
            # If not found, create an empty equivalent_courses.csv with header.
            empty_df = pd.DataFrame(columns=["Course", "Equivalent"])
            empty_df.to_csv("equivalent_courses.csv", index=False)
            upload_file(service, "equivalent_courses.csv", "equivalent_courses.csv")
            st.info("No equivalent courses file found on Google Drive. An empty file has been created and uploaded.")
    except Exception as e:
        st.error(f"Error processing equivalent courses file: {e}")

# --- Assignment Types Configuration Section (unchanged) ---
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types (e.g., S.C.E, F.E.C, ARAB201).")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
