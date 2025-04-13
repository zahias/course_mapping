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
from logging_utils import log_action
from google_drive_utils import authenticate_google_drive, download_file, search_file
from googleapiclient.discovery import build
from datetime import datetime
import os
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from config import get_allowed_assignment_types, GRADE_ORDER, extract_primary_grade_from_full_value, cell_color

st.title("View Reports")
st.markdown("---")

# Reload equivalent courses and course configuration from Google Drive
if st.button("Reload Equivalent Courses", help="Download the latest equivalent courses mapping from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, "equivalent_courses.csv")
        if file_id:
            download_file(service, file_id, "equivalent_courses.csv")
            st.success("Equivalent courses reloaded successfully.")
        else:
            st.error("Equivalent courses file not found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading equivalent courses: {e}")

if st.button("Reload Courses Configuration", help="Reload courses configuration from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        file_id = search_file(service, "courses_config.csv")
        if file_id:
            download_file(service, file_id, "courses_config.csv")
            st.success("Courses configuration reloaded successfully.")
        else:
            st.error("Courses configuration file not found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading courses configuration: {e}")

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
        eq_df = None
        if os.path.exists("equivalent_courses.csv"):
            eq_df = pd.read_csv("equivalent_courses.csv")
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process the report to get the full detailed view
        full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )

        # Append calculated credit columns from full_req_df if not already present
        credits_cols = ["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
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
        # (The credit summary columns remain unchanged, because their names are not in target_courses)

        # Toggle 1: Show All Grades (detailed) vs. Simplified Primary-Grade view.
        show_all_toggle = st.checkbox("Show All Grades", value=True, help="If checked, display detailed grade tokens with earned credits; if unchecked, display only the primary grade with its credit.")
        if show_all_toggle:
            displayed_req_df = full_req_df.copy()
            displayed_int_df = intensive_req_df.copy()
        else:
            displayed_req_df = primary_req_df.copy()
            displayed_int_df = primary_int_df.copy()

        # Toggle 2: Show Completed/Not Completed Only.
        # Apply the collapse only to the course columns (keys of target_courses), leaving the credit summary columns intact.
        show_complete_toggle = st.checkbox("Show Completed/Not Completed Only", value=False, help="If enabled, display 'c' for passed courses and blank for failed courses in the course columns.")
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

        st.markdown("**Color Legend:**")
        st.markdown("- Light Green: Passed courses")
        st.markdown("- Light Yellow: Currently Registered (CR) courses")
        st.markdown("- Pink: Not Completed/Failing courses")
        st.subheader("Assign Courses")
        st.markdown("Select one course per student for each assignment type from extra courses.")
        
        if st.button("Reset All Assignments", help="Clears all saved assignments"):
            reset_assignments()
            st.success("All assignments have been reset.")
            st.rerun()
        
        search_student = st.text_input("Search by Student ID or Name", help="Type to filter extra courses by student or course")
        extra_courses_df["ID"] = extra_courses_df["ID"].astype(str)
        for atype in allowed_assignment_types:
            extra_courses_df[atype] = False
        for idx, row in extra_courses_df.iterrows():
            sid = row["ID"]
            course = row["Course"]
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for atype in allowed_assignment_types:
                    if assigns.get(atype) == course:
                        extra_courses_df.at[idx, atype] = True
        if search_student:
            extra_courses_df = extra_courses_df[
                extra_courses_df["ID"].str.contains(search_student, case=False, na=False) |
                extra_courses_df["NAME"].str.contains(search_student, case=False, na=False)
            ]
        from ui_components import add_assignment_selection
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        errors, updated_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
        if errors:
            st.error("Please resolve the following issues before saving assignments:")
            for error in errors:
                st.write(f"- {error}")
        else:
            if st.button("Save Assignments", help="Save the updated assignments to Google Drive"):
                save_assignments(updated_assignments)
                st.success("Assignments saved.")
                st.rerun()
        
        if "# of Credits Completed" in full_req_df.columns and "# Remaining" in full_req_df.columns:
            summary_df = full_req_df[["ID", "NAME", "# of Credits Completed", "# Remaining"]].copy()
            fig = px.bar(
                summary_df,
                x="NAME",
                y=["# of Credits Completed", "# Remaining"],
                barmode="group",
                title="Completed vs. Remaining Credits per Student"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = save_report_with_formatting(displayed_req_df, displayed_int_df, timestamp)
        st.session_state["output"] = output.getvalue()
        from logging_utils import log_action
        log_action(f"Report generated at {timestamp}")
        st.download_button(
            label="Download Processed Report",
            data=st.session_state["output"],
            file_name="student_progress_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        import shutil, datetime
        def backup_files():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"backups/{ts}"
            os.makedirs(backup_folder, exist_ok=True)
            for f in ["equivalent_courses.csv", "sce_fec_assignments.csv", "courses_config.csv", "app.log"]:
                if os.path.exists(f):
                    shutil.copy(f, backup_folder)
        if st.button("Perform Manual Backup", help="Create a timestamped backup of key files"):
            backup_files()
            st.success("Backup completed.")
