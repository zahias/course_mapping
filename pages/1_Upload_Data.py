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
from googleapiclient.discovery import build
from logging_utils import setup_logging

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# -- Reload button --
if st.button("Reload Progress Report from Google Drive"):
    # Determine filename to reload
    fname = st.session_state.get("progress_filename", "progress_report.xlsx")
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, fname)
        if file_id:
            download_file(service, file_id, fname)
            df = read_progress_report(fname)
            if df is not None:
                st.session_state["raw_df"] = df
                st.success(f"Reloaded '{fname}' from Google Drive and processed successfully.")
            else:
                st.error(f"Reloaded '{fname}' but failed to parse it.")
        else:
            st.error(f"No file named '{fname}' found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading from Google Drive: {e}")

# -- File uploader --
uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report or the wide format."
)

if uploaded_file is not None:
    # Save locally
    filepath = save_uploaded_file(uploaded_file)
    # Remember filename for future reloads
    st.session_state["progress_filename"] = uploaded_file.name

    # Sync to Google Drive
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, uploaded_file.name)
        if file_id:
            update_file(service, file_id, filepath)
            st.info(f"Updated '{uploaded_file.name}' on Google Drive.")
        else:
            upload_file(service, filepath, uploaded_file.name)
            st.info(f"Uploaded '{uploaded_file.name}' to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing to Google Drive: {e}")

    # Read & validate
    df = read_progress_report(filepath)
    if df is not None:
        st.session_state["raw_df"] = df
        st.success("File uploaded and processed successfully. Move to 'Customize Courses' or 'View Reports'.")
    else:
        st.error("Failed to read data from the uploaded progress report.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
