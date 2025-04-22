import streamlit as st
import pandas as pd
import pandas.errors
from datetime import datetime
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
import os
from config import get_allowed_assignment_types, extract_primary_grade_from_full_value, cell_color

st.title("View Reports")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("Upload data first.")
    st.stop()

df = st.session_state['raw_df']
t_rules = st.session_state.get('target_course_rules')
i_rules = st.session_state.get('intensive_course_rules')
if t_rules is None or i_rules is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

# load assignments & equivalents
per_asg = load_assignments()
# handle empty equivalent file
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try: eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError: eq_df = pd.DataFrame(columns=['Course','Equivalent'])
else:
    eq_df = pd.DataFrame(columns=['Course','Equivalent'])
eq_map = read_equivalent_courses(eq_df) if not eq_df.empty else {}

# process
req_df, int_df, extra_df, _ = process_progress_report(df, t_rules, i_rules, per_asg, eq_map)

# append credit summaries
credit_map = {c: r[0]['Credits'] for c,r in t_rules.items()}
req_cred = req_df.apply(lambda r: calculate_credits(r, credit_map),axis=1)
req_df = pd.concat([req_df, req_cred],axis=1)
int_credit_map = {c: r[0]['Credits'] for c,r in i_rules.items()}
int_cred = int_df.apply(lambda r: calculate_credits(r, int_credit_map),axis=1)
int_df = pd.concat([int_df, int_cred],axis=1)

# simplified view
prim_req = req_df.copy()
for c in t_rules:
    prim_req[c] = prim_req[c].apply(lambda x: extract_primary_grade_from_full_value(x))
prim_int = int_df.copy()
for c in i_rules:
    prim_int[c] = prim_int[c].apply(lambda x: extract_primary_grade_from_full_value(x))

# toggles
show_all = st.checkbox("Show All Grades", value=True)
if show_all:
    disp_req = req_df.copy()
    disp_int = int_df.copy()
else:
    disp_req = prim_req.copy()
    disp_int = prim_int.copy()

show_c = st.checkbox("Show Completed/Not Completed Only", value=False)
if show_c:
    def colps(v):
        if not isinstance(v,str): return v
        parts = v.split('|')
        if len(parts)==2:
            num = parts[1].strip()
            try: return 'c' if int(num)>0 else ''
            except:
                return 'c' if num.upper()=='PASS' else ''
        return v
    for c in t_rules: disp_req[c] = disp_req[c].apply(colps)
    for c in i_rules: disp_int[c] = disp_int[c].apply(colps)

# display
display_dataframes(disp_req, disp_int, extra_df, df)

# legend
st.markdown(
  "<p><strong>Color Legend:</strong> "
  "<span style='background-color: lightgreen;'>Passed</span> "
  "<span style='background-color: #FFFACD;'>CR</span> "
  "<span style='background-color: pink;'>Not Passed</span></p>",
  unsafe_allow_html=True
)

# assignments
st.subheader("Assign Courses")
_ = st.text_input("Search by Student ID or Name")
edited = add_assignment_selection(extra_df)
c1,c2,c3 = st.columns(3)
save_b = c1.button("Save Assignments")
reset_b= c2.button("Reset All Assignments")
dl_b   = c3.button("Download Processed Report")

if reset_b:
    reset_assignments(); st.success("Reset."); st.experimental_rerun()

errs,upd = validate_assignments(edited, per_asg)
if errs:
    st.error("Resolve:"); [st.write(f"- {e}") for e in errs]
elif save_b:
    save_assignments(upd); st.success("Saved."); st.experimental_rerun()

if dl_b:
    out = save_report_with_formatting(disp_req, disp_int, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button("Download Excel", out.getvalue(),
                       "student_progress_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
