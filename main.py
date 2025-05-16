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

setup_logging()

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report or the wide format."
)

# --- Reload from Drive (moved directly below uploader) ---
if st.button("Reload Progress from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)

        # Look for any of the three names
        drive_id = None
        for name in ("progress_report.xlsx", "progress_report.xls", "progress_report.csv"):
            fid = search_file(service, name)
            if fid:
                drive_id = fid
                local = name
                break

        if drive_id:
            download_file(service, drive_id, local)
            df = read_progress_report(local)
            if df is not None:
                st.session_state["raw_df"] = df
                st.success(f"Reloaded '{local}' from Google Drive.")
            else:
                st.error("Downloaded file could not be parsed.")
        else:
            st.error("No progress_report.* found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading from Drive: {e}")

# --- Handle Upload & Sync ---
if uploaded_file is not None:
    # 1) Save locally
    filepath = save_uploaded_file(uploaded_file)

    # 2) Push to Drive under canonical name
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        ext = filepath.split(".")[-1].lower()
        drive_name = f"progress_report.{ext}"

        fid = search_file(service, drive_name)
        if fid:
            update_file(service, fid, filepath)
            st.info(f"Updated '{drive_name}' on Google Drive.")
        else:
            upload_file(service, filepath, drive_name)
            st.info(f"Uploaded '{drive_name}' to Google Drive.")
    except Exception as e:
        st.error(f"Error syncing to Google Drive: {e}")

    # 3) Parse and stash
    df = read_progress_report(filepath)
    if df is not None:
        st.session_state["raw_df"] = df
        st.success("File uploaded and processed successfully. Proceed to Customize Courses or View Reports.")
    else:
        st.error("Failed to read the uploaded file.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
