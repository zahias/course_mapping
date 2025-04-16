# main.py

import streamlit as st
import pandas as pd
from datetime import datetime

from utilities import save_uploaded_file
from data_processing import read_progress_report, process_progress_report, calculate_credits
from assignment_utils import load_assignments
from google_drive_utils import authenticate_google_drive, search_file, download_file
from logging_utils import setup_logging

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

# -- Header --
st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

setup_logging()

# -- DASHBOARD (new) --
if (
    'raw_df' in st.session_state
    and 'target_courses' in st.session_state
    and 'intensive_courses' in st.session_state
):
    df = st.session_state['raw_df']
    target = st.session_state['target_courses']
    intensive = st.session_state['intensive_courses']
    per_student_assignments = load_assignments()

    # No equivalent mapping here
    full_req_df, _, _, _ = process_progress_report(
        df, target, intensive, per_student_assignments, {}
    )

    # Append credit summaries
    credits = full_req_df.apply(lambda row: calculate_credits(row, target), axis=1)
    full_req_df = pd.concat([full_req_df, credits], axis=1)

    # Compute metrics
    total_students = full_req_df.shape[0]
    total_completed = int(full_req_df['# of Credits Completed'].sum())
    total_remaining = int(full_req_df['# Remaining'].sum())

    # Identify at‑risk (<50% completed)
    pct = full_req_df['# of Credits Completed'] / full_req_df['Total Credits']
    at_risk = full_req_df.loc[pct < 0.5, 'NAME'].tolist()

    # Display as three metric cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Students Processed", total_students)
    col2.metric("Total Credits Completed", total_completed)
    col3.metric("Total Credits Remaining", total_remaining)

    # At‑risk alert
    if at_risk:
        st.warning(f"At‑Risk Students ({len(at_risk)}): " + ", ".join(at_risk))

    # Quick links reminder
    st.markdown(
        "**Quick Links:** Use the sidebar to navigate to "
        "**Upload Data**, **Customize Courses**, **View Reports**, or **Student Profiles**."
    )

    st.markdown("---")

# -- UPLOAD SECTION (unchanged) --
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
    else:
        st.error("Failed to read data from the uploaded progress report.")
else:
    st.info("Please upload an Excel or CSV file to proceed.")
