import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from datetime import datetime
import os
from config import get_allowed_assignment_types, GRADE_ORDER, extract_primary_grade_from_full_value, cell_color
from google_drive_utils import authenticate_google_drive, download_file, search_file, upload_file
from googleapiclient.discovery import build

st.title("View Reports")
st.markdown("---")

# --- Equivalent Courses File Sync ---
# Check for the local "equivalent_courses.csv" file.
if not os.path.exists("equivalent_courses.csv"):
    # Create an empty DataFrame with the expected columns.
    empty_df = pd.DataFrame(columns=["Course", "Equivalent"])
    empty_df.to_csv("equivalent_courses.csv", index=False)
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        folder_id = None  # Modify here if you require a specific folder.
        # Search for the file on Google Drive.
        file_id = search_file(service, "equivalent_courses.csv", folder_id=folder_id)
        # If not found on Drive, upload the empty file.
        if not file_id:
            upload_file(service, "equivalent_courses.csv", "equivalent_courses.csv", folder_id=folder_id)
        st.info("Created empty 'equivalent_courses.csv' on Google Drive.")
    except Exception as e:
        st.error(f"Error creating 'equivalent_courses.csv' on Google Drive: {e}")
# Now load the file locally.
eq_df = pd.read_csv("equivalent_courses.csv")

# --- End Equivalent Courses Sync ---

if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
else:
    df = st.session_state["raw_df"]
    target_courses = st.session_state.get("target_courses")
    intensive_courses = st.session_state.get("intensive_courses")
    if target_courses is None or intensive_courses is None:
        st.warning("Courses not defined yet. Go to 'Customize Courses'.")
    else:
        per_student_assignments = load_assignments()
        # Process equivalent courses data
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process the report to get the full detailed view.
        full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )

        # Append calculated credit columns to full_req_df.
        credits_df = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        full_req_df = pd.concat([full_req_df, credits_df], axis=1)
        intensive_credits_df = intensive_req_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_req_df = pd.concat([intensive_req_df, intensive_credits_df], axis=1)

        # Precompute a simplified primary-grade view that preserves credit columns.
        primary_req_df = full_req_df.copy()
        for course in target_courses:
            primary_req_df[course] = primary_req_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))
        primary_int_df = intensive_req_df.copy()
        for course in intensive_courses:
            primary_int_df[course] = primary_int_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))

        # Toggle 1: Show All Grades vs. Simplified Primary-Grade view.
        show_all_toggle = st.checkbox("Show All Grades", value=True, help="Toggle between detailed (all grades with credits) and simplified (primary grade with credit) views.")
        if show_all_toggle:
            displayed_req_df = full_req_df.copy()
            displayed_int_df = intensive_req_df.copy()
        else:
            displayed_req_df = primary_req_df.copy()
            displayed_int_df = primary_int_df.copy()

        # Toggle 2: Show Completed/Not Completed Only.
        # In this mode, the course columns are replaced with "c" if passed, or blank if not passed.
        show_complete_toggle = st.checkbox("Show Completed/Not Completed Only", value=False, help="Display 'c' for passed courses; leave blank for failed courses, in the course columns.")
        if show_complete_toggle:
            def collapse_pass_fail(val):
                if not isinstance(val, str):
                    return val
                parts = val.split("|")
                if len(parts) == 2:
                    credit_str = parts[1].strip()
                    try:
                        num = int(credit_str)
                        return "c" if num > 0 else ""
                    except ValueError:
                        return "c" if credit_str.upper() == "PASS" else ""
                return val
            for col in target_courses.keys():
                displayed_req_df[col] = displayed_req_df[col].apply(collapse_pass_fail)
            for col in intensive_courses.keys():
                displayed_int_df[col] = displayed_int_df[col].apply(collapse_pass_fail)

        allowed_assignment_types = get_allowed_assignment_types()
        from ui_components import display_dataframes
        display_dataframes(
            displayed_req_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(target_courses.keys())]),
            displayed_int_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(intensive_courses.keys())]),
            extra_courses_df, df
        )

        # Display the color legend on one horizontal line.
        st.markdown(
            "<p><strong>Color Legend:</strong> "
            "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> "
            "<span style='margin-left: 10px; background-color: #FFFACD; padding: 3px 10px;'>CR (Currently Registered)</span> "
            "<span style='margin-left: 10px; background-color: pink; padding: 3px 10px;'>Not Completed/Failing</span></p>",
            unsafe_allow_html=True
        )

        st.subheader("Assign Courses")
        # Removed the instruction text as requested.
        # Arrange assignment section layout: a search bar, then the assignment table, then three buttons horizontally.
        search_bar = st.text_input("Search by Student ID or Name", help="Filter extra courses by student or course")
        from ui_components import add_assignment_selection
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            save_btn = st.button("Save Assignments", help="Save assignments to Google Drive")
        with btn_col2:
            reset_btn = st.button("Reset All Assignments", help="Clear all assignments")
        with btn_col3:
            download_btn = st.button("Download Processed Report", help="Download report", key="download_btn")
        
        if reset_btn:
            reset_assignments()
            st.success("All assignments have been reset.")
            st.experimental_rerun()
        
        from assignment_utils import validate_assignments
        errors, updated_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
        if errors:
            st.error("Please resolve the following issues before saving assignments:")
            for error in errors:
                st.write(f"- {error}")
        else:
            if save_btn:
                save_assignments(updated_assignments)
                st.success("Assignments saved.")
                st.experimental_rerun()
        
        if download_btn:
            output = save_report_with_formatting(displayed_req_df, displayed_int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
            st.session_state["output"] = output.getvalue()
            st.download_button(
                label="Download Processed Report",
                data=st.session_state["output"],
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Add a full-width footer with developer credit.
        st.markdown("<hr style='border:1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; font-size:14px;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
