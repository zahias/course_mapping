import pandas as pd
import streamlit as st
from config import is_passing_grade_from_list, get_allowed_assignment_types

# Academic semester ordering: Fall → Spring → Summer
SEM_ORDER = {"Fall": 1, "Spring": 2, "Summer": 3}

def read_progress_report(filepath):
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                missing = required_columns - set(df.columns)
                if missing:
                    st.error(f"Missing columns: {missing}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet; attempting wide‑format transform.")
                df = pd.read_excel(xls)
                return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing expected columns; attempting wide‑format transform.")
                return transform_wide_format(df)
        else:
            st.error("Unsupported file format. Upload Excel or CSV.")
            return None
    except Exception as e:
        st.error(f"Error reading progress report: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format requires 'STUDENT ID' and COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notna() & (df_melted['CourseData'] != '')]
    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE format.")
        return None
    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()
    sem_year = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year.shape[1] < 2:
        st.error("Semester-Year not recognized (e.g. 'FALL-2016').")
        return None
    df_melted['Semester'] = sem_year[0].str.title().str.strip()
    df_melted['Year'] = sem_year[1].astype(int)
    df_melted = df_melted.rename(columns={'STUDENT ID':'ID', 'NAME':'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(df_melted.columns):
        st.error(f"After transform missing: {req - set(df_melted.columns)}")
        return None
    return df_melted[['ID','NAME','Course','Grade','Year','Semester']].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    if equivalent_courses_df is None:
        return mapping
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping

def _term_to_tuple(year: int, semester: str):
    """Convert (year,semester) to a tuple that respects Fall→Spring→Summer order."""
    return (int(year), SEM_ORDER.get(semester.title(), 0))

def select_course_definition(defs: list, year: int, semester: str) -> dict:
    """
    From a list of course‐definition dicts (each with an optional Effective_From),
    pick the one whose Effective_From is the latest date <= the student’s term.
    If none apply, fall back to the definition with the earliest Effective_From.
    """
    term = _term_to_tuple(year, semester)
    candidates = []
    for d in defs:
        ef = d.get('Effective_From')
        if ef:
            ef_term = (ef[1], SEM_ORDER.get(ef[0], 0))
        else:
            ef_term = (0, 0)
        candidates.append((d, ef_term))
    # Definitions that have started by this term
    valid = [(d, t) for (d, t) in candidates if t <= term]
    if valid:
        # Choose the one whose start is most recent
        chosen = max(valid, key=lambda x: x[1])[0]
    else:
        # No definition started yet; use the earliest one
        chosen = min(candidates, key=lambda x: x[1])[0]
    return chosen

def determine_course_value(grade, course, courses_config, year, semester):
    """
    Time‐aware grade processing:
      - Null → 'NR'
      - Empty → 'CR | credits'
      - Otherwise split on ',', check passing via the selected definition's PassingGrades
    """
    defs = courses_config.get(course, [])
    if not defs:
        return 'NR'
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    pass_list = cfg['PassingGrades']
    if pd.isna(grade):
        return 'NR'
    if grade == '':
        return f'CR | {credits}'
    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, pass_list) for tok in tokens)
    token_str = ', '.join(tokens)
    if credits > 0:
        return f'{token_str} | {credits}' if passed else f'{token_str} | 0'
    else:
        return f'{token_str} | PASS' if passed else f'{token_str} | FAIL'

def process_progress_report(
    df: pd.DataFrame,
    target_cfg: dict,
    intensive_cfg: dict,
    per_student_assignments: dict = None,
    equivalent_courses_mapping: dict = None
):
    # 1) Apply equivalent‐course mapping
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 2) Apply S.C.E./F.E.C. assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID'])
            course = r['Course']
            for atype in allowed:
                if per_student_assignments.get(sid, {}).get(atype) == course:
                    return atype
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 3) Split into required, intensive, extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) & ~df['Mapped Course'].isin(intensive_cfg)]

    def pivot_and_apply(subdf, cfg_dict):
        # include Year & Semester to pick definitions
        piv = subdf.pivot_table(
            index=['ID','NAME','Year','Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # ensure all course columns exist
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # apply time‐aware determine_course_value
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c], c, cfg_dict, int(r['Year']), r['Semester']
                ),
                axis=1
            )
        # drop Year & Semester before returning
        return piv.drop(columns=['Year','Semester'])

    req_pivot = pivot_and_apply(req_df, target_cfg)
    int_pivot = pivot_and_apply(int_df, intensive_cfg)
    extra_list = sorted(extra_df['Course'].unique())

    return req_pivot, int_pivot, extra_df, extra_list

def calculate_credits(row, courses_config, year, semester):
    """
    Recalculate completed/registered/remaining/total credits
    using the time‐aware definition for each course.
    """
    completed = registered = remaining = total = 0
    for course, defs in courses_config.items():
        cfg = select_course_definition(defs, year, semester)
        cred = cfg['Credits']
        total += cred
        val = row.get(course, '')
        if isinstance(val, str) and val.upper().startswith('CR'):
            registered += cred
        elif isinstance(val, str) and val.upper().startswith('NR'):
            remaining += cred
        elif isinstance(val, str):
            parts = val.split('|')
            if len(parts) == 2:
                right = parts[1].strip()
                try:
                    num = int(right)
                    if num > 0:
                        completed += cred
                    else:
                        remaining += cred
                except ValueError:
                    if right.upper() != 'PASS':
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
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Required Courses"

    light_green = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    # Write Intensive sheet
    ws2 = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
