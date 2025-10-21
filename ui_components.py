import streamlit as st
import pandas as pd
from config import get_allowed_assignment_types

def _active_assignment_types():
    """
    Resolve the current assignment type list with per-Major override if present.
    """
    major = st.session_state.get("selected_major")
    if major:
        override = st.session_state.get(f"{major}_allowed_assignment_types")
        if isinstance(override, (list, tuple)) and len(override) > 0:
            return [str(x) for x in override if str(x).strip()]
    # Fallback to global/default
    return [str(x) for x in get_allowed_assignment_types()]

def display_dataframes(styled_df, intensive_styled_df, extra_courses_df, raw_df):
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])
    with tab1:
        st.subheader("Required Courses Progress Report")
        st.dataframe(styled_df, use_container_width=True)
    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.dataframe(intensive_styled_df, use_container_width=True)
    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.dataframe(extra_courses_df, use_container_width=True)

def add_assignment_selection(extra_courses_df: pd.DataFrame):
    """
    Displays an inline-editable table for extra courses assignments using st.data_editor.
    The available assignment types are resolved dynamically (per-Major) each render.
    """
    allowed_assignment_types = _active_assignment_types()

    # Ensure boolean columns exist for each assignment type
    for col in allowed_assignment_types:
        if col not in extra_courses_df.columns:
            extra_courses_df[col] = False

    # Base columns always shown
    base_cols = ['ID', 'NAME', 'Course', 'Grade']
    base_cols = [c for c in base_cols if c in extra_courses_df.columns]

    assignment_columns = base_cols + allowed_assignment_types

    # Force Streamlit to rebuild the editor when the set/order of types changes
    editor_key = "extra_courses_editor_" + "_".join(allowed_assignment_types)

    edited_df = st.data_editor(
        extra_courses_df[assignment_columns],
        num_rows="dynamic",
        use_container_width=True,
        key=editor_key
    )
    return edited_df
