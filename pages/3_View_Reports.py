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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
# 1) Ensure raw data & course lists
=======
>>>>>>> parent of 98d5b2a (3)
=======
# 1) Ensure raw data & course lists
>>>>>>> parent of abfac76 (3)
=======
>>>>>>> parent of dd799ab (Revert "4")
if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data first.")
    st.stop()
<<<<<<< HEAD
<<<<<<< HEAD
df = st.session_state["raw_df"]
target = st.session_state.get("target_courses")
intensive = st.session_state.get("intensive_courses")
rules = st.session_state.get("course_rules", {})
if target is None or intensive is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

<<<<<<< HEAD
# 2) Load assignments
per_student = load_assignments()

# 3) Load equivalent courses safely
=======

# Load raw data and course configs
=======
>>>>>>> parent of abfac76 (3)
df = st.session_state["raw_df"]
target = st.session_state.get("target_courses")
intensive = st.session_state.get("intensive_courses")
rules = st.session_state.get("course_rules", {})
if target is None or intensive is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

# 2) Load assignments
per_student = load_assignments()

<<<<<<< HEAD
# Load equivalent-courses CSV, handle empty
>>>>>>> parent of 98d5b2a (3)
=======
# 3) Load equivalent courses safely
>>>>>>> parent of abfac76 (3)
=======
per_assign = load_assignments()

# Load equivalent courses safely
>>>>>>> parent of dd799ab (Revert "4")
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try:
        eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=["Course","Equivalent"])
=======
# (Reload buttons have been removed because they are now in the Customize Courses page.)

if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
>>>>>>> parent of e37c21f (e)
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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
# 4) Process
full_req, full_int, extra_df, _ = process_progress_report(
    df,
    target,
    intensive,
    per_student_assignments=per_student,
    equivalent_courses_mapping=eq_map,
    course_rules=rules
)
=======
=======
# (Reload buttons have been removed because they are now in the Customize Courses page.)

<<<<<<< HEAD
if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
=======
# Static credits lookup (first definition’s credit)
credits_static = {c: defs[0]['Credits'] for c, defs in target_cfg.items()}

# Append credit summaries
credit_summ = req_df.apply(lambda r: calculate_credits(r, credits_static), axis=1)
req_df = pd.concat([req_df, credit_summ], axis=1)

# Primary‑grade precompute
primary_req = req_df.copy()
for c in target_cfg:
    primary_req[c] = primary_req[c].apply(lambda v: extract_primary_grade_from_full_value(v))

# Toggles
show_all = st.checkbox("Show All Grades", value=True)
show_comp = st.checkbox("Show Completed/Not Completed Only", value=False)

if show_all:
    disp_req = req_df.copy()
>>>>>>> parent of dd799ab (Revert "4")
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

<<<<<<< HEAD
>>>>>>> parent of e37c21f (e)
        # Process the report to get the full detailed view.
        full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )
        # Append calculated credit columns.
        credits_df = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        full_req_df = pd.concat([full_req_df, credits_df], axis=1)
        intensive_credits_df = intensive_req_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_req_df = pd.concat([intensive_req_df, intensive_credits_df], axis=1)
<<<<<<< HEAD
>>>>>>> parent of e37c21f (e)

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
        show_complete_toggle = st.checkbox("Show Completed/Not Completed Only", value=False, help="If enabled, displays 'c' for passed courses and blank for failed courses in course columns.")
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

<<<<<<< HEAD
# 8) Display
=======
# Process report with time‐aware passing rules
req_df, int_df, extra_df, _ = process_progress_report(
=======
# 4) Process
full_req, full_int, extra_df, _ = process_progress_report(
>>>>>>> parent of abfac76 (3)
    df,
    target,
    intensive,
    per_student_assignments=per_student,
    equivalent_courses_mapping=eq_map,
    course_rules=rules
)
=======
>>>>>>> parent of e37c21f (e)

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
        show_complete_toggle = st.checkbox("Show Completed/Not Completed Only", value=False, help="If enabled, displays 'c' for passed courses and blank for failed courses in course columns.")
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

<<<<<<< HEAD
<<<<<<< HEAD
def collapse(val):
    if not isinstance(val, str): return val
    parts = val.split("|")
    if len(parts)==2:
        p = parts[1].strip()
        try:
            return "c" if int(p)>0 else ""
        except:
            return "c" if p.upper()=="PASS" else ""
    return val

def prepare(df_full, df_prim):
    df = df_full if show_all else df_prim
    if show_only:
        for col in target_cfg:
            df[col] = df[col].apply(collapse)
        for col in intensive_cfg:
            df[col] = df[col].apply(collapse)
    return df

disp_req = prepare(req_df, prim_req)
disp_int = prepare(int_df, prim_int)

# Display
>>>>>>> parent of 98d5b2a (3)
display_dataframes(disp_req, disp_int, extra_df, df)

=======
if show_comp:
    def collapse(v):
        if not isinstance(v, str):
            return v
        parts = v.split("|")
        if len(parts)==2:
            right = parts[1].strip()
            try:
                return "c" if int(right)>0 else ""
            except ValueError:
                return "c" if right.upper()=="PASS" else ""
        return v
    for c in target_cfg:
        disp_req[c] = disp_req[c].apply(collapse)

# Display tables
display_dataframes(disp_req, int_df, extra_df, df)

# Color legend
>>>>>>> parent of dd799ab (Revert "4")
st.markdown(
<<<<<<< HEAD
=======
# 8) Display
display_dataframes(disp_req, disp_int, extra_df, df)

st.markdown(
>>>>>>> parent of abfac76 (3)
    "<p><strong>Legend:</strong> "
    "<span style='background-color:lightgreen;padding:3px;'>Passed</span> "
    "<span style='background-color:#FFFACD;padding:3px;'>CR</span> "
    "<span style='background-color:pink;padding:3px;'>Not Passed</span></p>",
<<<<<<< HEAD
=======
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding: 3px;'>Passed</span> "
    "<span style='background-color: #FFFACD; padding: 3px;'>CR</span> "
    "<span style='background-color: pink; padding: 3px;'>Not Passed</span></p>",
>>>>>>> parent of 98d5b2a (3)
=======
>>>>>>> parent of abfac76 (3)
    unsafe_allow_html=True
)
=======
        # Display the color legend on one horizontal line using HTML.
        st.markdown(
            "<p><strong>Color Legend:</strong> "
            "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> | "
            "<span style='background-color: #FFFACD; padding: 3px 10px;'>Currently Registered (CR)</span> | "
            "<span style='background-color: pink; padding: 3px 10px;'>Not Completed/Failing</span></p>",
            unsafe_allow_html=True
        )

        st.subheader("Assign Courses")
        # (Instruction text removed as requested.)
>>>>>>> parent of e37c21f (e)

        # Layout for the assignment section:
        # First, a search bar.
        search_bar = st.text_input("Search by Student ID or Name", help="Filter extra courses by student or course")
        
        # Then, display the assignment table.
        from ui_components import add_assignment_selection
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        
        # Finally, place three buttons on one horizontal line: Save Assignments, Reset All Assignments, Download Processed Report.
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
            st.rerun()
        
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
                st.rerun()
        
        # For downloading, if download button is pressed, force download.
        if download_btn:
            output = save_report_with_formatting(displayed_req_df, displayed_int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
            st.session_state["output"] = output.getvalue()
            st.download_button(
                label="Download Processed Report",
                data=st.session_state["output"],
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

<<<<<<< HEAD
c1,c2,c3 = st.columns(3)
<<<<<<< HEAD
<<<<<<< HEAD
save_btn = c1.button("Save Assignments")
reset_btn = c2.button("Reset All Assignments")
dl_btn    = c3.button("Download Processed Report")

if reset_btn:
    reset_assignments()
    st.success("Assignments reset.")
    st.experimental_rerun()

errs, updated = validate_assignments(edited, per_student)
if errs:
    st.error("Resolve errors:")
    for e in errs: st.write(f"- {e}")
=======
save_btn    = c1.button("Save Assignments")
reset_btn   = c2.button("Reset All Assignments")
download_btn= c3.button("Download Processed Report")
=======
save_btn = c1.button("Save Assignments")
reset_btn = c2.button("Reset All Assignments")
dl_btn    = c3.button("Download Processed Report")
>>>>>>> parent of abfac76 (3)

if reset_btn:
    reset_assignments()
    st.success("Assignments reset.")
    st.experimental_rerun()

<<<<<<< HEAD
errors, updated = validate_assignments(edited, per_student_assignments)
if errors:
<<<<<<< HEAD
    st.error("Resolve the following:")
    for e in errors:
        st.write(f"- {e}")
>>>>>>> parent of 98d5b2a (3)
=======
errs, updated = validate_assignments(edited, per_student)
if errs:
    st.error("Resolve errors:")
    for e in errs: st.write(f"- {e}")
>>>>>>> parent of abfac76 (3)
elif save_btn:
=======
    st.error("Resolve these errors:")
    for e in errors:
        st.write(f"- {e}")
elif save:
>>>>>>> parent of dd799ab (Revert "4")
    save_assignments(updated)
    st.success("Assignments saved.")
    st.experimental_rerun()

<<<<<<< HEAD
<<<<<<< HEAD
if dl_btn:
=======
if download_btn:
>>>>>>> parent of 98d5b2a (3)
=======
if dl_btn:
>>>>>>> parent of abfac76 (3)
    out = save_report_with_formatting(disp_req, disp_int, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button(
        "Download Excel",
        data=out.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

<<<<<<< HEAD
<<<<<<< HEAD
# 10) Footer
=======
>>>>>>> parent of 98d5b2a (3)
=======
# 10) Footer
>>>>>>> parent of abfac76 (3)
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
=======
        # (Plotly chart section removed as requested.)

        # Add a horizontal footer with developer credit.
        st.markdown("<hr style='border:1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; font-size:14px;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
>>>>>>> parent of e37c21f (e)
=======
        # Display the color legend on one horizontal line using HTML.
        st.markdown(
            "<p><strong>Color Legend:</strong> "
            "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> | "
            "<span style='background-color: #FFFACD; padding: 3px 10px;'>Currently Registered (CR)</span> | "
            "<span style='background-color: pink; padding: 3px 10px;'>Not Completed/Failing</span></p>",
            unsafe_allow_html=True
        )

        st.subheader("Assign Courses")
        # (Instruction text removed as requested.)

        # Layout for the assignment section:
        # First, a search bar.
        search_bar = st.text_input("Search by Student ID or Name", help="Filter extra courses by student or course")
        
        # Then, display the assignment table.
        from ui_components import add_assignment_selection
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        
        # Finally, place three buttons on one horizontal line: Save Assignments, Reset All Assignments, Download Processed Report.
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
            st.rerun()
        
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
                st.rerun()
        
        # For downloading, if download button is pressed, force download.
        if download_btn:
            output = save_report_with_formatting(displayed_req_df, displayed_int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
            st.session_state["output"] = output.getvalue()
            st.download_button(
                label="Download Processed Report",
                data=st.session_state["output"],
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # (Plotly chart section removed as requested.)

        # Add a horizontal footer with developer credit.
        st.markdown("<hr style='border:1px solid #ddd;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; font-size:14px;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
>>>>>>> parent of e37c21f (e)
