import os
import streamlit as st
import pandas as pd
from datetime import datetime
from utilities import save_uploaded_file
from data_processing import read_progress_report
from googleapiclient.discovery import build
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    upload_file,
    update_file,
    download_file
)
from logging_utils import setup_logging

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# --- Reload from Drive button ---
if st.button("Reload Progress Report from Google Drive"):
    fn = st.session_state.get("raw_filename")
    local_path = st.session_state.get("raw_filepath")
    if not fn or not local_path:
        st.error("No previously uploaded file name found. Please upload first.")
    else:
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            file_id = search_file(service, fn)
            if file_id:
                download_file(service, file_id, local_path)
                df = read_progress_report(local_path)
                if df is not None:
                    st.session_state["raw_df"] = df
                    st.success(f"Reloaded '{fn}' from Google Drive.")
                else:
                    st.error("Downloaded file could not be processed. Please check its format.")
            else:
                st.error(f"No file named '{fn}' found on Google Drive.")
        except Exception as e:
            st.error(f"Error reloading from Google Drive: {e}")

st.markdown("---")

# --- File uploader ---
uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report or the wide format."
)

if uploaded_file is not None:
    # 1) Save locally
    filepath = save_uploaded_file(uploaded_file)
    # 2) Read & validate
    df = read_progress_report(filepath)
    if df is not None:
        # store for downstream
        st.session_state["raw_df"] = df
        st.session_state["raw_filepath"] = filepath
        st.session_state["raw_filename"] = uploaded_file.name

        # 3) Sync to Google Drive
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            file_id = search_file(service, uploaded_file.name)
            if file_id:
                update_file(service, file_id, filepath)
            else:
                upload_file(service, filepath, uploaded_file.name)
            st.success(f"Uploaded and synced '{uploaded_file.name}' to Google Drive. Move to 'Customize Courses' or 'View Reports'.")
        except Exception as e:
            st.error(f"File processed locally, but failed to sync to Google Drive: {e}")
    else:
        st.error("Failed to read data from the uploaded progress report.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
