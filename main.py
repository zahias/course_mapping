# pages/1_Upload_Data.py

import os
from datetime import datetime

import pandas as pd
import streamlit as st
from googleapiclient.discovery import build

from utilities import save_uploaded_file
from data_processing import read_progress_report
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    upload_file,
    update_file,
    download_file
)
from logging_utils import setup_logging

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

# ——— Greeting ———
st.markdown("## Hello")
st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# ——— Layout for Reload vs Upload ———
col1, col2 = st.columns([3, 1])

# 1) Reload from Google Drive
with col2:
    if st.button("Reload Progress Report from Google Drive"):
        if "progress_file_name" not in st.session_state:
            st.error("No previously uploaded file to reload. Please upload first.")
        else:
            drive_name = st.session_state["progress_file_name"]
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                file_id = search_file(service, drive_name)
                if file_id:
                    os.makedirs("uploads", exist_ok=True)
                    local_path = os.path.join("uploads", drive_name)
                    download_file(service, file_id, local_path)

                    df = read_progress_report(local_path)
                    if df is not None:
                        st.session_state["raw_df"] = df
                        st.success(f"Reloaded '{drive_name}' from Google Drive and processed.")
                    else:
                        st.error("Downloaded file could not be read as a Progress Report.")
                else:
                    st.error(f"No file named '{drive_name}' found on Google Drive.")
            except Exception as e:
                st.error(f"Error reloading from Google Drive: {e}")

# 2) Upload new file
with col1:
    uploaded_file = st.file_uploader(
        "Upload Student Progress File (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        help="You can upload the standard Progress Report or the wide format."
    )
    if uploaded_file is not None:
        # save locally
        filepath = save_uploaded_file(uploaded_file)
        st.session_state["progress_file_name"] = uploaded_file.name

        # sync to Google Drive
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

        # read & store
        df = read_progress_report(filepath)
        if df is not None:
            st.session_state["raw_df"] = df
            st.success("File uploaded, processed, and synced. Move to 'Customize Courses' or 'View Reports'.")
        else:
            st.error("Failed to read data from the uploaded progress report.")

# 3) Prompt if nothing loaded yet
if "raw_df" not in st.session_state:
    st.info("Please upload an Excel or CSV file to proceed.")
