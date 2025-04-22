# data_processing.py

import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def read_progress_report(filepath):
    """
    Reads the uploaded progress report, handling both standard and wide formats.
    Returns a DataFrame with columns: ID, NAME, Course, Grade, Year, Semester
    or None on error.
    """
    try:
        lower = filepath.lower()
        if lower.endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_cols = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                missing = required_cols - set(df.columns)
                if missing:
                    st.error(f"Missing columns in 'Progress Report': {missing}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet found; trying wide format.")
                df = pd.read_excel(xls, sheet_name=0)
                return transform_wide_format(df)
        elif lower.endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing standard columns; trying wide format.")
                return transform_wide_format(df)
        else:
            st.error("Unrecognized file type. Upload XLSX, XLS, or CSV.")
            return None
    except Exception as e:
        st.error(f"Error reading progress report: {e}")
        return None

def transform_wide_format(df):
    """
    Transforms a wide‐format sheet (COURSE1, COURSE2, ... columns) into long form.
    Expects 'STUDENT ID' and 'NAME' columns.
    COURSEi entries like 'MATH102/SPRING-2018/F'.
    """
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format requires 'STUDENT ID' and COURSE* columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    # Melt
    melted = df.melt(id_vars=id_vars, value_name='CourseData')
    melted = melted[melted['CourseData'].notna() & (melted['CourseData']!='')]

    # Split CourseData
    parts = melted['CourseData'].str.split('/', expand=True)
    if parts.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE format.")
        return None
    melted['Course'] = parts[0].str.strip().str.upper()
    sem_year = parts[1].str.strip()
    melted['Grade'] = parts[2].str.strip().str.upper()

    sy = sem_year.str.split('-', expand=True)
    if sy.shape[1] < 2:
        st.error("Expected SEMESTER-YEAR in course data.")
        return None
    melted['Semester'] = sy[0].str.strip().str.title()
    melted['Year'] = sy[1].str.strip()

    melted = melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(melted.columns):
        st.error(f"Transformed data missing columns: {req - set(melted.columns)}")
        return None

    return melted[list(req)].drop_duplicates()

def read_equivalent_courses(equiv_df):
    """
    Given a DataFrame with columns 'Course' and 'Equivalent' (comma‑separated list),
    returns a dict mapping each equivalent → primary course.
    """
    mapping = {}
    for _, r in equiv_df.iterrows():
        primary = r['Course'].strip().upper()
        for eq in str(r['Equivalent']).split(','):
            mapping[eq.strip().upper()] = primary
    return mapping

def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None,
    course_rules=None
):
    """
    Processes the raw DataFrame into three outputs:
      - required_out: pivot table of ID/NAME × required courses with "grades | credits" cells
      - intensive_out: same for intensive courses
      - extra_df: flat DataFrame of extra courses for assignment
      - extra_list: list of unique extra course codes
    Uses semester‐effective passing rules from course_rules.
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # 1) Encode semester as numeric for comparisons
    sem_map = {'Spring':1, 'Summer':2, 'Fall':3}
    df['SemValue'] = df['Year'].astype(int)*10 + df['Semester'].map(sem_map)

    # 2) Map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) Apply per‐student S.C.E./F.E.C. assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def assign_map(r):
            sid, orig, mapped = str(r['ID']), r['Course'], r['Mapped Course']
            assigns = per_student_assignments.get(sid, {})
            for t in allowed:
                if assigns.get(t) == orig:
                    return t
            return mapped
        df['Mapped Course'] = df.apply(assign_map, axis=1)

    # 4) Determine pass/fail per row using effective rules
    def passed_flag(r):
        code, grade, sv = r['Mapped Course'], str(r['Grade']).upper(), r['SemValue']
        rules = course_rules.get(code, [])
        # pick the last rule whose eff <= sv
        applicable = [rl for rl in rules if rl['eff'] <= sv]
        if applicable:
            rule = max(applicable, key=lambda x: x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return grade in rule['passing_grades']

    df['PassedFlag'] = df.apply(passed_flag, axis=1)

    # 5) Split into required/intensive/extra
    extra_df = df[
        ~df['Mapped Course'].isin(target_courses) &
        ~df['Mapped Course'].isin(intensive_courses)
    ]
    req_df = df[df['Mapped Course'].isin(target_courses)]
    int_df = df[df['Mapped Course'].isin(intensive_courses)]

    # 6) Pivot grades & flags
    grades_req = req_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()
    flags_req = req_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    grades_int = int_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()
    flags_int = int_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # 7) Ensure all columns present
    for c in target_courses:
        if c not in grades_req: grades_req[c] = None
        if c not in flags_req:  flags_req[c]  = False
    for c in intensive_courses:
        if c not in grades_int: grades_int[c] = None
        if c not in flags_int:  flags_int[c]  = False

    # 8) Merge grade tokens + credits
    def merge_row(gr_row, fl_row, course_dict):
        out = {}
        for course, cred in course_dict.items():
            gs = gr_row.get(course) or ''
            ok = bool(fl_row.get(course))
            if gs == '':
                cell = 'NR'
            else:
                cell = f"{gs} | {cred if ok else 0}"
            out[course] = cell
        return out

    req_out = grades_req[['ID','NAME']].copy()
    for i, row in grades_req.iterrows():
        merged = merge_row(row, flags_req.iloc[i], target_courses)
        for k,v in merged.items():
            req_out.at[i,k] = v

    int_out = grades_int[['ID','NAME']].copy()
    for i, row in grades_int.iterrows():
        merged = merge_row(row, flags_int.iloc[i], intensive_courses)
        for k,v in merged.items():
            int_out.at[i,k] = v

    extra_list = sorted(extra_df['Course'].unique())
    return req_out, int_out, extra_df, extra_list

def calculate_credits(row, courses_dict):
    """
    Given a pivoted row, calculates:
      # of Credits Completed, # Registered (CR), # Remaining, Total Credits.
    """
    completed = registered = remaining = 0
    total = sum(courses_dict.values())
    for course, cred in courses_dict.items():
        val = row.get(course, '')
        if isinstance(val, str):
            up = val.upper()
            if up.startswith('CR'):
                registered += cred
            elif up.startswith('NR'):
                remaining += cred
            else:
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
                        # PASS/FAIL for 0-credit courses
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

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    """
    Exports the two displayed DataFrames to an Excel bytes buffer,
    applying color fills based on cell values.
    """
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Required Courses"
    green = PatternFill(start_color='90EE90',end_color='90EE90',fill_type='solid')
    pink  = PatternFill(start_color='FFC0CB',end_color='FFC0CB',fill_type='solid')
    yellow= PatternFill(start_color='FFFACD',end_color='FFFACD',fill_type='solid')

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True),1):
        for c_idx, val in enumerate(row,1):
            cell = ws1.cell(row=r_idx,column=c_idx,value=val)
            if r_idx==1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = green
                elif '#FFFACD' in style:
                    cell.fill = yellow
                else:
                    cell.fill = pink

    # Intensive sheet
    ws2 = wb.create_sheet("Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True),1):
        for c_idx, val in enumerate(row,1):
            cell = ws2.cell(row=r_idx,column=c_idx,value=val)
            if r_idx==1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = green
                elif '#FFFACD' in style:
                    cell.fill = yellow
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
