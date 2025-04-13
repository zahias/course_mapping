import streamlit as st
import pandas as pd
import os
from google_drive_utils import authenticate_google_drive, search_file, download_file, upload_file
from googleapiclient.discovery import build

st.set_page_config(page_title="Customize Courses", layout="wide")
st.title("Customize Courses")

st.write(
    "Upload a custom CSV file for your courses configuration. It must include the columns: "
    "'Course', 'Credits', 'PassingGrades', and 'Type'. "
    "For example, the PassingGrades for ARAB201 might be: A+,A,A-,B+,B,B-,C+,C,C-."
)

with st.expander("Courses Configuration Options", expanded=True):
    uploaded_courses = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="Use the provided template or your own configuration."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template", help="Download a CSV template for courses configuration"):
            template_df = pd.DataFrame({
                'Course': ['ENGL201', 'CHEM201', 'ARAB201', 'MATH101'],
                'Credits': [3, 3, 3, 3],
                'PassingGrades': ['A+,A,A-', 'A+,A,A-', 'A+,A,A-,B+,B,B-,C+,C,C-', 'A+,A,A-,B+,B,B-,C+,C,C-'],
                'Type': ['Required', 'Required', 'Required', 'Required']
            })
            csv_data = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Courses Template", data=csv_data, file_name='courses_template.csv', mime='text/csv')
    with col2:
        if st.button("Reload Courses Configuration", help="Reload the courses configuration from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    download_file(service, file_id, "courses_config.csv")
                    st.success("Courses configuration reloaded from Google Drive.")
                else:
                    st.info("No configuration file found on Google Drive. Uploading your local copy.")
                    if uploaded_courses is not None:
                        with open("courses_config.csv", "wb") as f:
                            f.write(uploaded_courses.getbuffer())
                        upload_file(service, "courses_config.csv", "courses_config.csv")
                        st.success("Courses configuration uploaded to Google Drive.")
            except Exception as e:
                st.error(f"Error reloading configuration: {e}")

    # Load courses configuration: prefer uploaded file; else, local file.
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
            courses_df.to_csv("courses_config.csv", index=False)
        except Exception as e:
            st.error(f"Error reading uploaded configuration: {e}")
            courses_df = None
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    if courses_df is not None:
        req_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if req_cols.issubset(courses_df.columns):
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            required_df = courses_df[courses_df['Type'].str.lower() == 'required']
            intensive_df = courses_df[courses_df['Type'].str.lower() == 'intensive']
            target_courses = {}
            for _, row in required_df.iterrows():
                target_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrades": row['PassingGrades']
                }
            intensive_courses = {}
            for _, row in intensive_df.iterrows():
                intensive_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrades": row['PassingGrades']
                }
            st.session_state['target_courses'] = target_courses
            st.session_state['intensive_courses'] = intensive_courses

            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if not file_id:
                    upload_file(service, "courses_config.csv", "courses_config.csv")
                    st.info("Courses configuration uploaded to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing configuration to Google Drive: {e}")
            st.success("Courses configuration loaded successfully.")
        else:
            st.error("The configuration file must contain: Course, Credits, PassingGrades, and Type.")
    else:
        st.info("No courses configuration loaded. Please upload a configuration file.")

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
            st.info("No equivalent courses file found on Google Drive.")
    except Exception as e:
        st.error(f"Error loading equivalent courses: {e}")

with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Enter the comma-separated assignment types (for example, S.C.E, F.E.C, ARAB201).")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Assignment Types", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")

st.markdown("<hr style='border: none; height: 2px; background-color: #aaa;'/>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 14px;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
