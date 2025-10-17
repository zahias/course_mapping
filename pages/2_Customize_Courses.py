# 2_Customize_Courses.py

import streamlit as st
import pandas as pd
from utilities import merge_courses_config_and_table

st.title("Customize Courses")

st.markdown(
    "Upload your **Courses Configuration** (rules: credits, type, requisites) and "
    "optionally a **Courses Table** (names, offered) to build a single combined catalog."
)

config_file = st.file_uploader("Courses Configuration (Excel)", type=["xlsx", "xls"])
table_file = st.file_uploader("Courses Table (Excel, optional)", type=["xlsx", "xls"])

if "courses_df" not in st.session_state:
    st.session_state.courses_df = pd.DataFrame()

if st.button("Build / Update Catalog"):
    if not config_file:
        st.error("Please upload a Courses Configuration file.")
    else:
        try:
            config_df = pd.read_excel(config_file)
            table_df = pd.read_excel(table_file) if table_file else None
            merged = merge_courses_config_and_table(config_df, table_df)
            st.session_state.courses_df = merged
            st.success("Combined courses catalog updated.")
        except Exception as e:
            st.error(f"Failed to build catalog: {e}")

if not st.session_state.courses_df.empty:
    st.subheader("Combined Courses Catalog")
    st.dataframe(st.session_state.courses_df, use_container_width=True)
else:
    st.info("No combined catalog yet. Upload files and click **Build / Update Catalog**.")
