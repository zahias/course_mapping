import pandas as pd
import streamlit as st
<<<<<<< HEAD
from config import is_passing_grade_from_list, get_allowed_assignment_types
<<<<<<< HEAD
=======
from config import get_default_grading_system
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment
import io

# Semester ordering for comparisons
SEM_ORDER = {'Fall': 1, 'Spring': 2, 'Summer': 3}


def read_progress_report(filepath):
    """
    Reads an uploaded Excel or CSV and returns a normalized DataFrame
    with columns: ID, NAME, Course, Grade, Year (int), Semester ('Spring','Summer','Fall').
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required.issubset(df.columns):
                    st.error(f"Missing columns: {required - set(df.columns)}")
                    return None
                return df
            # fallback to wide
            df = pd.read_excel(xls)
            return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            return transform_wide_format(df)
        else:
            st.error("Unsupported file type.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def transform_wide_format(df):
    """
    Transforms a 'wide' student‑courses sheet (with COURSE1, COURSE2, ... columns)
    into the normalized long format.
    """
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Cannot parse wide format: missing 'STUDENT ID' or COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    melted = melted[melted['CourseData'].notna() & (melted['CourseData'] != '')]
    parts = melted['CourseData'].str.split('/', expand=True)
    if parts.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE in wide data.")
        return None

    melted['Course'] = parts[0].str.strip().str.upper()
    melted['Semester_Year'] = parts[1].str.strip()
    melted['Grade'] = parts[2].str.strip().str.upper()

    sy = melted['Semester_Year'].str.split('-', expand=True)
    if sy.shape[1] < 2:
        st.error("Expected SEMESTER-YEAR format like 'FALL-2016'.")
        return None
    melted['Semester'] = sy[0].str.strip().str.title()
    melted['Year'] = sy[1].str.strip()

    melted = melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})
    required = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required.issubset(melted.columns):
        st.error(f"Missing after transform: {required - set(melted.columns)}")
        return None

    melted['Year'] = melted['Year'].astype(int, errors='ignore')
    return melted[list(required)].drop_duplicates()


def read_equivalent_courses(equivalent_courses_df):
    """
    From a DataFrame with columns ['Course','Equivalent'], builds a mapping
    of each equivalent -> primary Course.
    """
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        eqs = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in eqs:
            mapping[eq] = primary
    return mapping
>>>>>>> parent of 5a48a63 (Update data_processing.py)
=======
from config import get_allowed_assignment_types
>>>>>>> parent of 98d5b2a (3)

# Semester index for computing a linear code: FALL→0, SPRING→1, SUMMER→2
SEM_INDEX = {'Fall': 0, 'Spring': 1, 'Summer': 2}

def select_config(defs, record_code):
    """
    From a list of definitions, select the one whose [Eff_From, Eff_To]
    range includes record_code. If multiple, pick the one with the largest Eff_From.
    """
    candidates = []
    for d in defs:
        ef = d['Eff_From']
        et = d['Eff_To']
        ok_from = (ef is None) or (record_code >= ef)
        ok_to   = (et is None) or (record_code <= et)
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
        # pick the one with max Eff_From (None→treated as 0)
        return max(candidates, key=lambda d: d['Eff_From'] or 0)
    # fallback
    return defs[0]

def determine_course_value(grade_str, course, cfg_list, record_code):
    """
    Determine the cell value for a single course pivot:
      - Picks the config entry valid at record_code
      - Then applies passing‐grade logic to grade_str tokens
      - Uses Credits from that config entry
    """
    if pd.isna(grade_str):
        return "NR"
    if grade_str=="":
        cfg = select_config(cfg_list, record_code)
        return f"CR | {cfg['Credits']}"

    cfg = select_config(cfg_list, record_code)
    credits = cfg['Credits']
    passing = [g.strip().upper() for g in cfg['PassingGrades'].split(',')]

    tokens = [g.strip().upper() for g in grade_str.split(',') if g.strip()]
    tok_display = ", ".join(tokens)
    passed = any(tok in passing for tok in tokens)

    if credits > 0:
        return f"{tok_display} | {credits}" if passed else f"{tok_display} | 0"
    else:
        return f"{tok_display} | PASS" if passed else f"{tok_display} | FAIL"

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _, row in equiv_df.iterrows():
        prim = row['Course'].strip().upper()
        equivs = [e.strip().upper() for e in str(row['Equivalent']).split(',')]
        for e in equivs:
            mapping[e] = prim
    return mapping

def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    # 1) Compute a record code per row
    df['RecordCode'] = df.apply(
        lambda r: int(r['Year']) * 3 + SEM_INDEX[r['Semester']],
        axis=1
    )

    # 2) Map equivalent courses
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 3) Apply S.C.E./F.E.C. assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(row):
            sid = str(row['ID'])
            crs = row['Course']
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for t in allowed:
                    if assigns.get(t)==crs:
                        return t
            return row['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 4) Split into required/intensive/extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) &
                  ~df['Mapped Course'].isin(intensive_cfg)]

    # 5) Build pivots for grades and for record‐code
    grade_piv_req = req_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='Grade',
        aggfunc=lambda x: ", ".join(x.astype(str))
    ).reset_index()
    code_piv_req = req_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='RecordCode',
        aggfunc='max'
    ).reset_index().fillna(0)

    grade_piv_int = int_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='Grade',
        aggfunc=lambda x: ", ".join(x.astype(str))
    ).reset_index()
    code_piv_int = int_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='RecordCode',
        aggfunc='max'
    ).reset_index().fillna(0)

    # 6) Ensure all columns exist & apply determine_course_value
    def finalize(piv_grad, piv_code, cfg_dict):
        for course in cfg_dict.keys():
            if course not in piv_grad.columns:
                piv_grad[course] = None
            # apply time‐aware logic
            piv_grad[course] = piv_grad.apply(
                lambda r: determine_course_value(
                    r[course],
                    course,
                    cfg_dict[course],
                    int(piv_code.at[r.name, course] if course in piv_code else 0)
                ),
                axis=1
            )
        return piv_grad[['ID','NAME'] + list(cfg_dict.keys())]

    req_final = finalize(grade_piv_req, code_piv_req, target_cfg)
    int_final = finalize(grade_piv_int, code_piv_int, intensive_cfg)

<<<<<<< HEAD
    return req_piv, int_piv, extra_df, sorted(extra_df['Course'].unique())

def calculate_credits(row, credits_dict):
    """
    Static credit summation. credits_dict maps course->credit (int).
    """
    completed = registered = remaining = 0
    total = sum(credits_dict.values())
    for course, cred in credits_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            u = val.upper()
            if u.startswith("CR"):
                registered += cred
            elif u.startswith("NR"):
                remaining += cred
            else:
                right = val.split("|")[-1].strip()
                try:
                    num = int(right)
                    if num > 0:
                        completed += cred
                    else:
                        remaining += cred
                except ValueError:
                    if right.upper() == "PASS":
                        # 0‐credit passed
                        pass
                    else:
                        remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits']
    )
<<<<<<< HEAD
=======


def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    """
    Writes two sheets ('Required Courses', 'Intensive Courses') to an XLSX in memory,
    applying light-green fill for passed credits, pink for missing/failed, and yellow for CR.
    """
    output = io.BytesIO()
    wb = Workbook()

    # Prepare fills
    green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    yellow = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")

    def write_sheet(ws, df):
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    if isinstance(val, str):
                        u = val.upper()
                        if u.startswith("CR"):
                            cell.fill = yellow
                        else:
                            parts = val.split("|")
                            if len(parts) == 2:
                                right = parts[1].strip()
                                try:
                                    num = int(right)
                                    cell.fill = green if num > 0 else pink
                                except:
                                    cell.fill = green if right.upper() == "PASS" else pink
                            else:
                                cell.fill = pink
                    else:
                        cell.fill = pink

    ws1 = wb.active
    ws1.title = "Required Courses"
    write_sheet(ws1, displayed_df)

    ws2 = wb.create_sheet(title="Intensive Courses")
    write_sheet(ws2, intensive_displayed_df)

    wb.save(output)
    output.seek(0)
    return output
>>>>>>> parent of 5a48a63 (Update data_processing.py)
=======
    extra_list = sorted(extra_df['Course'].unique())
    return req_final, int_final, extra_df, extra_list
>>>>>>> parent of 98d5b2a (3)
