import pandas as pd
import streamlit as st
from config import is_passing_grade_from_list, get_allowed_assignment_types
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


def select_course_definition(defs, year, sem):
    """
    Given a list of definitions for a course (with Effective_From/To),
    picks the one valid for the given (year, sem).
    """
    candidates = []
    for d in defs:
        ef, et = d['Effective_From'], d['Effective_To']
        ok_from = True
        if ef:
            e_sem, e_yr = ef
            if (year < e_yr) or (year == e_yr and SEM_ORDER[sem] < SEM_ORDER[e_sem]):
                ok_from = False
        ok_to = True
        if et:
            t_sem, t_yr = et
            if (year > t_yr) or (year == t_yr and SEM_ORDER[sem] > SEM_ORDER[t_sem]):
                ok_to = False
        if ok_from and ok_to:
            candidates.append(d)

    if candidates:
        # pick the one with latest Effective_From
        def keyfn(x):
            ef = x['Effective_From']
            if not ef:
                return (0, 0)
            s, y = ef
            return (y, SEM_ORDER[s])
        return max(candidates, key=keyfn)

    # fallback
    return defs[0]


def determine_course_value(grade, course, courses_cfg, year, semester):
    """
    Uses time‑aware configuration to decide:
    - 'NR'
    - 'CR | credits'
    - 'TOKENS | credits' or 'TOKENS | 0'
    - 'TOKENS | PASS/FAIL' for zero‑credit courses
    """
    defs = courses_cfg.get(course, [])
    if not defs:
        return "NR"
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    passing = cfg['PassingGrades']

    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}"

    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, passing) for tok in tokens)
    tokstr = ", ".join(tokens)

    if credits > 0:
        return f"{tokstr} | {credits}" if passed else f"{tokstr} | 0"
    else:
        return f"{tokstr} | PASS" if passed else f"{tokstr} | FAIL"


def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def assign_map(r):
            sid, crs = str(r['ID']), r['Course']
            if sid in per_student_assignments:
                for a in allowed:
                    if per_student_assignments[sid].get(a) == crs:
                        return a
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(assign_map, axis=1)

    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[
        ~df['Mapped Course'].isin(target_cfg) &
        ~df['Mapped Course'].isin(intensive_cfg)
    ]

    def pivot_and_process(subdf, cfg_dict):
        piv = subdf.pivot_table(
            index=['ID', 'NAME', 'Year', 'Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()

        for course in cfg_dict:
            if course not in piv.columns:
                piv[course] = None

        for course in cfg_dict:
            piv[course] = piv.apply(
                lambda r: determine_course_value(
                    r[course], course, cfg_dict,
                    int(r['Year']), r['Semester']
                ),
                axis=1
            )

        return piv[['ID', 'NAME'] + list(cfg_dict.keys())]

    req_piv = pivot_and_process(req_df, target_cfg)
    int_piv = pivot_and_process(int_df, intensive_cfg)

    return req_piv, int_piv, extra_df, sorted(extra_df['Course'].unique())


def calculate_credits(row, credits_dict):
    """
    Summarizes # of Credits Completed, # Registered, # Remaining, and Total Credits.
    """
    completed = registered = remaining = 0
    total = sum(credits_dict.values())

    for course, cred in credits_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            up = val.upper()
            if up.startswith("CR"):
                registered += cred
            elif up.startswith("NR"):
                remaining += cred
            else:
                parts = val.split("|")
                if len(parts) == 2:
                    right = parts[1].strip()
                    try:
                        num = int(right)
                        if num > 0:
                            completed += cred
                        else:
                            remaining += cred
                    except ValueError:
                        if right.upper() == "PASS":
                            pass
                        else:
                            remaining += cred
                else:
                    remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits']
    )


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
