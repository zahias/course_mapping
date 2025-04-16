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
from config import (
    get_allowed_assignment_types,
    extract_primary_grade_from_full_value,
    cell_color
)

def view_reports_page():
    st.image("pu_logo.png", width=120)
    st.title("View Reports")

    if 'raw_df' not in st.session_state:
        st.warning("Upload data first.")
        return

    df = st.session_state['raw_df']
    target = st.session_state['target_courses']
    intensive = st.session_state['intensive_courses']
    assignments = load_assignments()
    eq_df = None
    if os.path.exists("equivalent_courses.csv"):
        eq_df = pd.read_csv("equivalent_courses.csv")
    eq_map = read_equivalent_courses(eq_df) if eq_df is not None else {}

    req_df, int_df, extra_df, _ = process_progress_report(df, target, intensive, assignments, eq_map)
    # Append credits…
    credits = req_df.apply(lambda r: calculate_credits(r, target), axis=1)
    req_df = pd.concat([req_df, credits], axis=1)
    int_credits = int_df.apply(lambda r: calculate_credits(r, intensive), axis=1)
    int_df = pd.concat([int_df, int_credits], axis=1)

    # Precompute primary-grade view
    primary_req = req_df.copy()
    for c in target: primary_req[c] = primary_req[c].map(extract_primary_grade_from_full_value)
    primary_int = int_df.copy()
    for c in intensive: primary_int[c] = primary_int[c].map(extract_primary_grade_from_full_value)

    # Toggles
    show_all = st.checkbox("Show All Grades", True)
    show_comp = st.checkbox("Show Completed/Not Completed Only", False)

    if show_all:
        disp_req, disp_int = req_df, int_df
    else:
        disp_req, disp_int = primary_req, primary_int

    if show_comp:
        def collapse(v):
            if not isinstance(v,str): return v
            parts = v.split("|")
            if len(parts)==2:
                right=parts[1].strip()
                try: return "c" if int(right)>0 else ""
                except: return "c" if right.upper()=="PASS" else ""
            return v
        for col in target: disp_req[col]=disp_req[col].map(collapse)
        for col in intensive: disp_int[col]=disp_int[col].map(collapse)

    display_dataframes(
        disp_req.style.applymap(cell_color, subset=pd.IndexSlice[:,list(target.keys())]),
        disp_int.style.applymap(cell_color, subset=pd.IndexSlice[:,list(intensive.keys())]),
        extra_df, df
    )

    st.markdown(
        "<p><strong>Color Legend:</strong> "
        "<span style='background-color: lightgreen; padding:3px;'>Passed</span> "
        "<span style='background-color: #FFFACD; padding:3px;'>CR</span> "
        "<span style='background-color: pink; padding:3px;'>Not Passed</span></p>",
        unsafe_allow_html=True
    )

    st.subheader("Assign Courses")
    search = st.text_input("Search by ID or Name")
    edited = add_assignment_selection(extra_df)

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Save Assignments"):
            errs, updated = validate_assignments(edited, assignments)
            if errs:
                st.error("\n".join(errs))
            else:
                save_assignments(updated)
                st.success("Assignments saved.")
    with c2:
        if st.button("Reset All Assignments"):
            reset_assignments()
            st.success("Assignments reset.")
    with c3:
        if st.button("Download Processed Report"):
            out = save_report_with_formatting(disp_req, disp_int, pd.Timestamp.now().strftime("%Y%m%d_%H%M%S"))
            st.download_button("Download", data=out.getvalue(), file_name="report.xlsx")

