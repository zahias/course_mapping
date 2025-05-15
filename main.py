import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utilities import save_uploaded_file
from data_processing import read_progress_report
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    download_file,
    upload_file,
    update_file
)
from logging_utils import setup_logging

st.set_page_config(
    page_title="Phoenicia University Student Progress Tracker",
    layout="wide"
)

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# --- Upload or Reload ---
col1, col2 = st.columns([3,1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload Student Progress File (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        help="You can upload the standard Progress Report or the wide format."
    )

with col2:
    if st.button("Reload Progress from Google Drive"):
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            # Try each possible extension
            for remote_name in ["progress_report.xlsx", "progress_report.xls", "progress_report.csv"]:
                file_id = search_file(service, remote_name)
                if file_id:
                    download_file(service, file_id, remote_name)
                    df = read_progress_report(remote_name)
                    if df is not None:
                        st.session_state["raw_df"] = df
                        st.success(f"Loaded `{remote_name}` from Google Drive.")
                    else:
                        st.error(f"Failed to read `{remote_name}` after download.")
                    break
            else:
                st.error("No progress report file found on Google Drive.")
        except Exception as e:
            st.error(f"Error reloading from Google Drive: {e}")

# --- Handle Upload ---
if uploaded_file is not None:
    # Save locally
    local_path = save_uploaded_file(uploaded_file)
    df = read_progress_report(local_path)
    if df is not None:
        # Persist in session
        st.session_state["raw_df"] = df
        st.success("File uploaded and processed successfully. Move to 'Customize Courses' or 'View Reports'.")

        # Sync to Google Drive
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            # Determine remote filename
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            remote_name = f"progress_report{ext}"
            # Upload or update
            file_id = search_file(service, remote_name)
            if file_id:
                update_file(service, file_id, local_path)
            else:
                upload_file(service, local_path, remote_name)
            st.info(f"Synchronized `{remote_name}` to Google Drive.")
        except Exception as e:
            st.error(f"Error syncing to Google Drive: {e}")
    else:
        st.error("Failed to read data from the uploaded progress report.")
elif "raw_df" not in st.session_state:
    st.info("Please upload an Excel or CSV file to proceed.")
