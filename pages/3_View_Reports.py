import streamlit as st
import pandas as pd
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

st.title("View Reports")
st.markdown("---")

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

        # Load equivalent courses mapping
        eq_df = None
        if os.path.exists("equivalent_courses.csv"):
            eq_df = pd.read_csv("equivalent_courses.csv")
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process the report
        full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )

        # Calculate credits
        credits_df = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        full_req_df = pd.concat([full_req_df, credits_df], axis=1)
        intensive_credits_df = intensive_req_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_req_df = pd.concat([intensive_req_df, intensive_credits_df], axis=1)

        # Build primary‐grade view
        primary_req_df = full_req_df.copy()
        for course in target_courses:
            primary_req_df[course] = primary_req_df[course].apply(extract_primary_grade_from_full_value)
        primary_int_df = intensive_req_df.copy()
        for course in intensive_courses:
            primary_int_df[course] = primary_int_df[course].apply(extract_primary_grade_from_full_value)

        # Toggles
        show_all_toggle = st.checkbox(
            "Show All Grades", value=True,
            help="Detailed vs. primary‐only grade view"
        )
        if show_all_toggle:
            displayed_req_df = full_req_df.copy()
            displayed_int_df = intensive_req_df.copy()
        else:
            displayed_req_df = primary_req_df.copy()
            displayed_int_df = primary_int_df.copy()

        show_complete_toggle = st.checkbox(
            "Show Completed/Not Completed Only",
            value=False,
            help="If enabled, shows 'c' or blank instead of grades"
        )
        if show_complete_toggle:
            def collapse_pass_fail(val):
                if not isinstance(val, str):
                    return val
                parts = val.split("|")
                if len(parts) == 2:
                    cs = parts[1].strip()
                    try:
                        return "c" if int(cs) > 0 else ""
                    except:
                        return "c" if cs.upper() == "PASS" else ""
                return val

            for col in target_courses:
                displayed_req_df[col] = displayed_req_df[col].apply(collapse_pass_fail)
            for col in intensive_courses:
                displayed_int_df[col] = displayed_int_df[col].apply(collapse_pass_fail)

        # Show the tables
        display_dataframes(
            displayed_req_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(target_courses.keys())]),
            displayed_int_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(intensive_courses.keys())]),
            extra_courses_df,
            df
        )

        # Color legend
        st.markdown(
            "<p><strong>Color Legend:</strong> "
            "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> | "
            "<span style='background-color: #FFFACD; padding: 3px 10px;'>Currently Registered (CR)</span> | "
            "<span style='background-color: pink; padding: 3px 10px;'>Not Completed/Failing</span></p>",
            unsafe_allow_html=True
        )

        # ---- ASSIGN COURSES SECTION ----
        st.subheader("Assign Courses")

        # 1) Search bar
        search_bar = st.text_input(
            "Search by Student ID, Name, or Course",
            help="Filter extra courses by text"
        )

        # 2) Apply the search filter to extra_courses_df
        if search_bar:
            extra_courses_df = extra_courses_df[
                extra_courses_df['ID'].astype(str).str.contains(search_bar, case=False, na=False) |
                extra_courses_df['NAME'].str.contains(search_bar, case=False, na=False) |
                extra_courses_df['Course'].str.contains(search_bar, case=False, na=False)
            ]

        # 3) Editable assignment table
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)

        # 4) Action buttons in one row
        btn1, btn2, btn3 = st.columns(3)
        with btn1:
            save_btn = st.button("Save Assignments", help="Save to Google Drive")
        with btn2:
            reset_btn = st.button("Reset All Assignments", help="Clear all assignments")
        with btn3:
            download_btn = st.button(
                "Download Processed Report",
                help="Download report",
                key="download_btn"
            )

        if reset_btn:
            reset_assignments()
            st.success("All assignments have been reset.")
            st.rerun()

        # 5) Validate & save
        errors, updated_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
        if errors:
            st.error("Resolve these before saving:")
            for err in errors:
                st.write(f"- {err}")
        elif save_btn:
            save_assignments(updated_assignments)
            st.success("Assignments saved.")
            st.rerun()

        # 6) Download if requested
        if download_btn:
            out = save_report_with_formatting(
                displayed_req_df, displayed_int_df,
                datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            st.session_state["output"] = out.getvalue()
            st.download_button(
                label="Download Processed Report",
                data=st.session_state["output"],
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Footer
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center; font-size:14px;'>"
            "Developed by Dr. Zahi Abdul Sater"
            "</div>",
            unsafe_allow_html=True
        )
