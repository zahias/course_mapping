import streamlit as st
from utilities import save_uploaded_file
from data_processing import read_progress_report
from logging_utils import setup_logging

def upload_data_page():
    st.image("pu_logo.png", width=120)
    st.title("Upload Student Progress File")
    setup_logging()

    uploaded_file = st.file_uploader(
        "Drag & drop or click to upload Progress Report (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        help="Standard 'Progress Report' sheet or wide format."
    )

    if uploaded_file:
        filepath = save_uploaded_file(uploaded_file)
        df = read_progress_report(filepath)
        if df is not None:
            st.session_state['raw_df'] = df
            st.success("File uploaded and processed successfully.")
        else:
            st.error("Failed to read the uploaded progress report.")
    else:
        st.info("Please upload an Excel or CSV file to proceed.")
