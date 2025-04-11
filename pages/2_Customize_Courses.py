import streamlit as st
import pandas as pd
import os
from google_drive_utils import authenticate_google_drive, search_file, download_file
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV for courses configuration. The CSV must contain these columns: "
    "'Course', 'Credits', 'Type' (Required or Intensive), and 'PassingGrade'. "
    "For 'PassingGrade', list all acceptable passing grades separated by commas. "
    "For example: A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T"
)

with st.expander("Course Configuration Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Courses Configuration (CSV)", type="csv", help="Use the template below.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template", help="Download a CSV template for courses configuration."):
            template_df = pd.DataFrame({
                'Course': ['ENGL201', 'CHEM201', 'ARAB201', 'MATH101'],
                'Credits': [3, 3, 3, 3],
                'Type': ['Required', 'Required', 'Required', 'Required'],
                'PassingGrade': ['A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T']
            })
            csv_data = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Courses Template", data=csv_data, file_name='courses_template.csv', mime='text/csv')
    with col2:
        if st.button("Reload Courses Configuration", help="Reload courses configuration from Google Drive"):
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
    
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
            courses_df = None
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    if courses_df is not None:
        required_cols = {'Course', 'Credits', 'Type', 'PassingGrade'}
        if required_cols.issubset(courses_df.columns):
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            required_df = courses_df[courses_df['Type'].str.lower() == 'required']
            intensive_df = courses_df[courses_df['Type'].str.lower() == 'intensive']
            target_courses = {}
            for _, row in required_df.iterrows():
                target_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrade": row['PassingGrade']
                }
            intensive_courses = {}
            for _, row in intensive_df.iterrows():
                intensive_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrade": row['PassingGrade']
                }
            st.session_state['target_courses'] = target_courses
            st.session_state['intensive_courses'] = intensive_courses
            st.success("Courses configuration loaded successfully.")
        else:
            st.error("CSV must contain 'Course', 'Credits', 'Type', and 'PassingGrade' columns.")
    else:
        st.info("No courses configuration available. Please upload a CSV or reload from Google Drive.")

with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types that can be assigned. For example, enter: S.C.E, F.E.C, ARAB201")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
