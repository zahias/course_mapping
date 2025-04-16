import streamlit as st
import pandas as pd
from datetime import datetime
from utilities import save_uploaded_file
from data_processing import read_progress_report
from google_drive_utils import authenticate_google_drive, download_file
from logging_utils import setup_logging

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

uploaded_file = st.file_uploader(
    "Upload Student Progress File (Excel/CSV)",
    type=["xlsx", "xls", "csv"],
    help="You can upload the standard Progress Report or the wide format."
)

setup_logging()

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
