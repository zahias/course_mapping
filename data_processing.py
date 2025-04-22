# data_processing.py

import pandas as pd
import streamlit as st
from config import is_passing_grade_from_list, get_allowed_assignment_types
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment
import io

# Define semester ordering for comparisons
SEM_ORDER = {'Fall': 1, 'Spring': 2, 'Summer': 3}


def read_progress_report(filepath):
    """
    Read an Excel/CSV Progress Report (long or wide format) into a DataFrame
    with columns ['ID','NAME','Course','Grade','Year','Semester'].
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required = {'ID','NAME','Course','Grade','Year','Semester'}
                if not required.issubset(df.columns):
                    st.error(f"Missing columns: {required - set(df.columns)}")
                    return None
                return df
            df = pd.read_excel(xls)  # fallback to wide
            return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course','Grade','Year','Semester'}.issubset(df.columns):
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
    Convert a wide‐format sheet (with COURSE1/COURSE2 columns)
    into the long form with columns ID, NAME, Course, Grade, Year, Semester.
    """
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format requires 'STUDENT ID' and COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    melted = df.melt(id_vars=id_vars, var_name='CourseCol', value_name='CourseData')
    melted = melted[melted['CourseData'].notna() & (melted['CourseData']!='')]

    parts = melted['CourseData'].str.split('/', expand=True)
    if parts.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE in wide data.")
        return None

    melted['Course']   = parts[0].str.strip().str.upper()
    sem_year           = parts[1].str.strip().str.split('-', expand=True)
    melted['Semester'] = sem_year[0].str.strip().str.title()
    melted['Year']     = sem_year[1].astype(int, errors='ignore')
    melted['Grade']    = parts[2].str.strip().str.upper()

    melted = melted.rename(columns={'STUDENT ID':'ID','NAME':'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(melted.columns):
        st.error(f"After transform, missing: {req - set(melted.columns)}")
        return None

    return melted[list(req)].drop_duplicates()


def read_equivalent_courses(equiv_df):
    """
    Build a dict mapping each equivalent course -> its primary course.
    """
    mapping = {}
    for _, row in equiv_df.iterrows():
        primary = row['Course'].strip().upper()
        for eq in str(row['Equivalent']).split(','):
            mapping[eq.strip().upper()] = primary
    return mapping


def select_course_definition(defs, year, sem):
    """
    From a list of course‐definitions (with Effective_From/Effective_To tuples),
    return the one applicable for (year,sem). If multiple match, pick the one
    with the latest Effective_From; if none match, fallback to defs[0].
    """
    candidates = []
    for d in defs:
        ef, et = d['Effective_From'], d['Effective_To']
        ok_from = True
        if ef:
            e_sem, e_yr = ef
            if (year < e_yr) or (year==e_yr and SEM_ORDER[sem] < SEM_ORDER[e_sem]):
                ok_from = False
        ok_to = True
        if et:
            t_sem, t_yr = et
            if (year > t_yr) or (year==t_yr and SEM_ORDER[sem] > SEM_ORDER[t_sem]):
                ok_to = False
        if ok_from and ok_to:
            candidates.append(d)

    if candidates:
        def keyfn(x):
            ef = x['Effective_From']
            return (0,0) if not ef else (ef[1], SEM_ORDER[ef[0]])
        return max(candidates, key=keyfn)

    return defs[0]


def determine_course_value(grade, course, courses_cfg, year, semester):
    """
    Using time‐aware config, return:
      - "NR" if missing,
      - "CR | credits" if registered,
      - "TOKENS | credits" or "TOKENS | 0" if a graded, credit‐bearing course,
      - "TOKENS | PASS/FAIL" if zero‐credit.
    """
    defs = courses_cfg.get(course, [])
    if not defs:
        return "NR"
    cfg = select_course_definition(defs, year, semester)
    cr, passing = cfg['Credits'], cfg['PassingGrades']

    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {cr}"

    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, passing) for tok in tokens)
    tokstr = ", ".join(tokens)

    if cr > 0:
        return f"{tokstr} | {cr}" if passed else f"{tokstr} | 0"
    else:
        return f"{tokstr} | PASS" if passed else f"{tokstr} | FAIL"


def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_mapping=None
):
    # 1) map equivalents
    if equivalent_mapping is None:
        equivalent_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_mapping.get(x, x))

    # 2) apply dynamic assignments (S.C.E./F.E.C./…)
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid, crs = str(r['ID']), r['Course']
            if sid in per_student_assignments:
                for a in allowed:
                    if per_student_assignments[sid].get(a) == crs:
                        return a
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 3) split into required, intensive, extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[
        ~df['Mapped Course'].isin(target_cfg) &
        ~df['Mapped Course'].isin(intensive_cfg)
    ]

    # 4) pivot ONLY on ID & NAME
    def pivot_and_grade(subdf, cfg_dict):
        piv = subdf.pivot_table(
            index=['ID','NAME'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()

        # ensure every column exists
        for course in cfg_dict:
            if course not in piv.columns:
                piv[course] = None

        # apply time‐aware grading (we need Year/Sem for each row,
        # so merge them back from subdf):
        # build a helper dict of the first Year/Sem for each student
        first_sem = subdf.drop_duplicates(['ID','NAME'])[['ID','NAME','Year','Semester']].set_index(['ID','NAME']).to_dict('index')
        def grade_cell(r, course):
            yr_sem = first_sem.get((r['ID'], r['NAME']), {'Year':None,'Semester':None})
            return determine_course_value(r[course], course, cfg_dict, yr_sem['Year'], yr_sem['Semester'])

        for course in cfg_dict:
            piv[course] = piv.apply(lambda r: grade_cell(r, course), axis=1)

        return piv[['ID','NAME'] + list(cfg_dict.keys())]

    req_piv = pivot_and_grade(req_df, target_cfg)
    int_piv = pivot_and_grade(int_df, intensive_cfg)

    extra_list = sorted(extra_df['Course'].unique())
    return req_piv, int_piv, extra_df, extra_list


def calculate_credits(row, credits_dict):
    """
    Summarizes completed, registered, remaining, and total credits.
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
                        n = int(right)
                        if n > 0:
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
        index=['# of Credits Completed','# Registered','# Remaining','Total Credits']
    )


def save_report_with_formatting(displayed_df, intensive_df, timestamp):
    """
    Write two Excel sheets with color coding.
    """
    out = io.BytesIO()
    wb = Workbook()
    green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink  = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    yellow= PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")

    def write_sheet(ws, df):
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    if isinstance(val, str) and val.upper().startswith("CR"):
                        cell.fill = yellow
                    elif isinstance(val, str) and "|" in val:
                        right = val.split("|")[1].strip()
                        try:
                            num = int(right)
                            cell.fill = green if num > 0 else pink
                        except:
                            cell.fill = green if right.upper()=="PASS" else pink
                    else:
                        cell.fill = pink

    ws1 = wb.active
    ws1.title = "Required Courses"
    write_sheet(ws1, displayed_df)

    ws2 = wb.create_sheet(title="Intensive Courses")
    write_sheet(ws2, intensive_df)

    wb.save(out)
    out.seek(0)
    return out
