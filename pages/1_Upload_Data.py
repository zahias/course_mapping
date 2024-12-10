import streamlit as st
import pandas as pd
import os
from datetime import datetime
from config import get_default_target_courses, get_default_grading_system, get_intensive_courses
from utilities import save_uploaded_file
from data_processing import read_progress_report
from logging_utils import setup_logging, log_action
from google_drive_utils import authenticate_google_drive, search_file, download_file
from googleapiclient.discovery import build

st.title("Upload Data")
st.markdown("---")

st.write("Upload the student progress report and ensure that the equivalent courses file is loaded from Google Drive.")

def load_equivalent_courses_file(file_path='equivalent_courses.csv'):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    file_id = search_file(service, file_path)
    if file_id:
        download_file(service, file_id, file_path)
        try:
            equivalent_courses_df = pd.read_csv(file_path)
            return equivalent_courses_df
        except Exception as e:
            st.error(f"Error reading equivalent courses file: {e}")
            return None
    else:
        st.warning("No equivalent courses file found on Google Drive.")
        return None

setup_logging()

if st.button("Reload Equivalent Courses", help="Click to reload the equivalent courses mapping from Google Drive"):
    eq_df = load_equivalent_courses_file()
    if eq_df is not None:
        st.sidebar.success("Equivalent courses mapping reloaded.")
        st.rerun()
    else:
        st.sidebar.warning("Failed to load equivalent courses mapping.")

uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report or the wide format."
)

if uploaded_file is not None:
    filepath = save_uploaded_file(uploaded_file)
    df = read_progress_report(filepath)
    if df is not None:
        st.session_state['raw_df'] = df
        st.success("File uploaded and processed successfully. Move to 'Customize Courses' or 'View Reports'.")
        log_action("Data file uploaded and processed.")
    else:
        st.error("Failed to read data from the uploaded progress report.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
