import streamlit as st
import pandas as pd
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

# --- Upload & Reload Controls ---
col1, col2 = st.columns([3, 1])
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

            # look for any of the three possible filenames
            drive_file_id = None
            for name in ["progress_report.xlsx", "progress_report.xls", "progress_report.csv"]:
                fid = search_file(service, name)
                if fid:
                    drive_file_id = fid
                    local_name = name
                    break

            if drive_file_id:
                download_file(service, drive_file_id, local_name)
                df = read_progress_report(local_name)
                if df is not None:
                    st.session_state["raw_df"] = df
                    st.success(f"Progress report reloaded from Google Drive ({local_name}).")
                else:
                    st.error("Failed to parse the downloaded progress report.")
            else:
                st.error("No progress_report file found on Google Drive.")
        except Exception as e:
            st.error(f"Error reloading from Google Drive: {e}")

setup_logging()

if uploaded_file is not None:
    # 1) Save locally
    filepath = save_uploaded_file(uploaded_file)

    # 2) Sync to Google Drive under standardized name
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        ext = filepath.split(".")[-1].lower()
        drive_name = f"progress_report.{ext}"

        file_id = search_file(service, drive_name)
        if file_id:
            update_file(service, file_id, filepath)
            st.info(f"Updated {drive_name} on Google Drive.")
        else:
            upload_file(service, filepath, drive_name)
            st.info(f"Uploaded {drive_name} to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing to Google Drive: {e}")

    # 3) Read & store DataFrame
    df = read_progress_report(filepath)
    if df is not None:
        st.session_state["raw_df"] = df
        st.success("File uploaded and processed successfully. Move to 'Customize Courses' or 'View Reports'.")
    else:
        st.error("Failed to read data from the uploaded progress report.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
