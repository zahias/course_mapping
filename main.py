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

st.set_page_config(
    page_title="Phoenicia University Student Progress Tracker",
    layout="wide",
)

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# Two‐column layout: uploader (wide) and reload button (narrow)
col_upload, col_reload = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload Student Progress File (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        help="You can upload the standard Progress Report or the wide format."
    )

with col_reload:
    reload_pressed = st.button("Reload From Google Drive")

# --- Handle Reload ---
if reload_pressed:
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        found = False
        # Try common filenames/extensions
        for ext in ("xlsx", "xls", "csv"):
            remote_name = f"progress_report.{ext}"
            file_id = search_file(service, remote_name)
            if file_id:
                download_file(service, file_id, remote_name)
                df = read_progress_report(remote_name)
                if df is not None:
                    st.session_state["raw_df"] = df
                    st.success(f"Reloaded `{remote_name}` from Google Drive.")
                else:
                    st.error(f"Downloaded `{remote_name}` but failed to parse it.")
                found = True
                break
        if not found:
            st.error("No `progress_report.(xlsx|xls|csv)` file found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading from Google Drive: {e}")

# --- Handle Upload ---
if uploaded_file is not None:
    # 1) Save locally
    local_path = save_uploaded_file(uploaded_file)
    # 2) Read & validate
    df = read_progress_report(local_path)
    if df is not None:
        st.session_state["raw_df"] = df
        st.success("File uploaded and processed successfully. Move to 'Customize Courses' or 'View Reports'.")

        # 3) Sync up to Google Drive
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)

            # Use a consistent remote name
            ext = os.path.splitext(local_path)[1].lower().lstrip(".")
            remote_name = f"progress_report.{ext}"

            file_id = search_file(service, remote_name)
            if file_id:
                update_file(service, file_id, local_path)
                st.info(f"Updated `{remote_name}` on Google Drive.")
            else:
                upload_file(service, local_path, remote_name)
                st.info(f"Uploaded `{remote_name}` to Google Drive.")
        except Exception as e:
            st.error(f"Error syncing to Google Drive: {e}")
    else:
        st.error("Failed to read data from the uploaded progress report.")

# --- Prompt if nothing loaded ---
elif "raw_df" not in st.session_state:
    st.info("Please upload a progress report or reload one from Google Drive to proceed.")
