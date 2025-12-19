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
import os

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# === 0) Major Selection ===
if "selected_major" not in st.session_state:
    st.session_state["selected_major"] = None

# List of available majors. Adjust this list as needed.
MAJOR_LIST = ["— select a major —", "PBHL", "SPTH-OLD", "SPTH-NEW", "NURS"]
major = st.selectbox("Select Major", MAJOR_LIST, index=0)

if major == "— select a major —":
    st.info("Please select a Major before uploading or reloading a progress report.")
    st.stop()

st.session_state["selected_major"] = major

# Ensure local folder for this major exists
local_folder = os.path.join("configs", major)
os.makedirs(local_folder, exist_ok=True)

# === 1) File Uploader ===
uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report (sheet named 'Progress Report') or the wide format. "
         "Supported formats:\n"
         "- Long format: Columns: ID, NAME, Course, Grade, Year, Semester\n"
         "- Wide format: ID/NAME columns + COURSE_* columns with values like 'CODE/SEM-YYYY/GRADE'"
)

# Show file format info if file is uploaded
if uploaded_file is not None:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext in ["xlsx", "xls"]:
        st.info(f"📄 **File detected:** Excel format ({file_ext.upper()}) - Will check for 'Progress Report' sheet or auto-detect format")
    elif file_ext == "csv":
        st.info(f"📄 **File detected:** CSV format - Will auto-detect long or wide format")

# === 2) Reload from Google Drive (immediately under uploader) ===
if st.button("Reload Progress from Google Drive"):
    with st.spinner("🔄 Connecting to Google Drive..."):
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)

            # Look for any of the three extensions under "configs/{major}/progress_report.*"
            drive_id = None
            drive_filename = None
            with st.spinner("🔍 Searching for progress report on Google Drive..."):
                for ext in ("xlsx", "xls", "csv"):
                    candidate = f"configs/{major}/progress_report.{ext}"
                    fid = search_file(service, candidate)
                    if fid:
                        drive_id = fid
                        drive_filename = candidate
                        break

            if drive_id:
                with st.spinner(f"⬇️ Downloading '{drive_filename}'..."):
                    local_path = os.path.join(local_folder, os.path.basename(drive_filename))
                    download_file(service, drive_id, local_path)

                with st.spinner("📊 Processing file..."):
                    df = read_progress_report(local_path)
                    if df is not None:
                        st.session_state[f"{major}_raw_df"] = df
                        st.success(f"✅ Reloaded '{drive_filename}' from Google Drive. ({len(df)} records)")
                    else:
                        st.error("Downloaded file could not be parsed as a Progress Report.")
            else:
                st.error("No `progress_report.*` found on Google Drive for this Major.")
        except Exception as e:
            st.error(f"Error reloading from Google Drive: {e}")

# === 3) Handle new Upload & Sync to Google Drive ===
if uploaded_file is not None:
    # 3a) Save locally under `configs/{major}/`
    local_path = os.path.join(local_folder, uploaded_file.name)
    with open(local_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 3b) Sync to Drive under canonical name `configs/{major}/progress_report.<ext>`
    with st.spinner("☁️ Syncing to Google Drive..."):
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)

            ext = uploaded_file.name.split(".")[-1].lower()
            drive_name = f"configs/{major}/progress_report.{ext}"

            file_id = search_file(service, drive_name)
            if file_id:
                update_file(service, file_id, local_path)
                st.info(f"✅ Updated '{drive_name}' on Google Drive.")
            else:
                upload_file(service, local_path, drive_name)
                st.info(f"✅ Uploaded '{drive_name}' to Google Drive.")
        except Exception as e:
            st.error(f"Error syncing progress report to Google Drive: {e}")

    # 3c) Parse & store DataFrame as session state under key "{major}_raw_df"
    with st.spinner("📊 Processing uploaded file..."):
        df = read_progress_report(local_path)
        if df is not None:
            st.session_state[f"{major}_raw_df"] = df
            st.success(f"✅ File uploaded and processed successfully! ({len(df)} records found) You may now proceed to Customize Courses or View Reports.")
        else:
            st.error("Failed to read the uploaded progress report file.")
else:
    st.info("Please upload a valid Excel or CSV file to proceed.")
