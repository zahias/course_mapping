# 5_Advising.py  (NEW PAGE)

import streamlit as st
import pandas as pd

# Import from the advising package (folder)
from advising import student_eligibility_view, full_student_view, render_advising_history

def _ready():
    if 'courses_df' not in st.session_state or st.session_state.courses_df is None or st.session_state.courses_df.empty:
        st.warning("Courses table is not loaded yet. Please upload/prepare data on the main page.")
        return False
    if 'progress_df' not in st.session_state or st.session_state.progress_df is None or st.session_state.progress_df.empty:
        st.warning("Progress report is not loaded yet. Please upload/prepare data on the main page.")
        return False
    if 'advising_selections' not in st.session_state:
        st.session_state['advising_selections'] = {}
    return True

st.set_page_config(page_title="Advising", layout="wide")
st.title("Advising")

if not _ready():
    st.stop()

tab1, tab2, tab3 = st.tabs(["Student Eligibility View", "Full Student View", "Advising Sessions"])

with tab1:
    student_eligibility_view()

with tab2:
    full_student_view()

with tab3:
    # History panel (save/read/delete advising snapshots)
    render_advising_history()
