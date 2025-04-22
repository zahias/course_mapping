import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def read_progress_report(filepath):
    """
    Reads an uploaded Progress Report (Excel or CSV) and returns a normalized DataFrame
    with columns: ID, NAME, Course, Grade, Year, Semester.
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required_columns.issubset(df.columns):
                    st.error(f"Missing columns: {required_columns - set(df.columns)}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet found. Attempting wide-format transform.")
                df = pd.read_excel(xls)
                df = transform_wide_format(df)
                if df is None:
                    st.error("Wide-format transformation failed.")
                return df

        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing expected columns. Attempting wide-format transform.")
                df = transform_wide_format(df)
                return df

        else:
            st.error("Unsupported file type. Please upload .xlsx, .xls, or .csv.")
            return None

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def transform_wide_format(df):
    """
    Converts a 'wide' style sheet into the long format with ID, NAME, Course, Grade, Year, Semester.
    Expects 'STUDENT ID', 'NAME', and columns named COURSE1, COURSE2, etc. containing 'CODE/SEM-YEAR/GRADE'.
    """
    if 'STUDENT ID' not in df.columns or not any(col.startswith('COURSE') for col in df.columns):
        st.error("Wide-format file missing 'STUDENT ID' or COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notnull() & (df_melted['CourseData'] != '')]

    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Could not parse course data (expect CODE/SEMESTER-YEAR/GRADE).")
        return None

    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()

    sem_year_split = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized (expect FALL-2016).")
        return None

    df_melted['Semester'] = sem_year_split[0].str.strip().str.title()
    df_melted['Year'] = sem_year_split[1].str.strip()

    df_melted = df_melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})

    required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required_columns.issubset(df_melted.columns):
        st.error(f"Missing columns after transform: {required_columns - set(df_melted.columns)}")
        return None

    df_final = df_melted[['ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester']].drop_duplicates()
    return df_final


def read_equivalent_courses(equivalent_courses_df):
    """
    Given a DataFrame with columns ['Course','Equivalent'], returns a dict mapping
    each equivalent course code → primary course code.
    """
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
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
    Processes the raw long‐format progress DataFrame into three outputs:
      1. Required courses pivot: ID, NAME, each target course → "grade tokens | credits" or "NR"
      2. Intensive courses pivot: same structure for intensive_courses
      3. extra_courses_df: flat DataFrame of courses not in target or intensive
      4. extra_courses_list: sorted list of those extra course codes

    Uses:
      - equivalent_courses_mapping to map course codes
      - per_student_assignments for S.C.E./F.E.C overrides
      - course_rules to decide passing based on semester
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # 1) numeric semester value
    sem_map = {'Spring': 1, 'Summer': 2, 'Fall': 3}
    df['SemValue'] = df['Year'].astype(int) * 10 + df['Semester'].map(sem_map)

    # 2) apply equivalent mapping
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) apply S.C.E./F.E.C. assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID'])
            orig = r['Course']
            mapped = r['Mapped Course']
            if sid in per_student_assignments:
                for atype in allowed:
                    if per_student_assignments[sid].get(atype) == orig:
                        return atype
            return mapped
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 4) determine pass/fail via effective rules
    def passed_flag(r):
        course = r['Mapped Course']
        grade = str(r['Grade']).strip().upper()
        sv = r['SemValue']
        rules = course_rules.get(course, [])
        # pick rule with highest eff <= sv
        appl = [rule for rule in rules if rule['eff'] <= sv]
        if appl:
            rule = max(appl, key=lambda x: x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return grade in rule['passing_grades']

    df['PassedFlag'] = df.apply(passed_flag, axis=1)

    # 5) split into extra / target / intensive
    extra_df = df[
        (~df['Mapped Course'].isin(target_courses)) &
        (~df['Mapped Course'].isin(intensive_courses))
    ]
    targ_df = df[df['Mapped Course'].isin(target_courses)]
    inten_df = df[df['Mapped Course'].isin(intensive_courses)]

    # 6) pivot grades & flags
    pivot_grades = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()

    pivot_passed = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    ipg = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()

    ipp = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # 7) ensure all columns exist
    for course in target_courses:
        if course not in pivot_grades: pivot_grades[course] = None
        if course not in pivot_passed: pivot_passed[course] = False
    for course in intensive_courses:
        if course not in ipg: ipg[course] = None
        if course not in ipp: ipp[course] = False

    # 8) assemble final grade|credit strings
    def make_cells(gr_row, fl_row, course_dict):
        out = {}
        for course, cred in course_dict.items():
            gs = gr_row.get(course) or ''
            ok = bool(fl_row.get(course))
            if gs == '':
                out[course] = 'NR'
            else:
                out[course] = f"{gs} | {cred if ok else 0}"
        return out

    # required output
    req_out = pivot_grades[['ID','NAME']].copy()
    for i, row in pivot_grades.iterrows():
        cells = make_cells(row, pivot_passed.iloc[i], target_courses)
        for c,v in cells.items():
            req_out.at[i,c] = v

    # intensive output
    int_out = ipg[['ID','NAME']].copy()
    for i, row in ipg.iterrows():
        cells = make_cells(row, ipp.iloc[i], intensive_courses)
        for c,v in cells.items():
            int_out.at[i,c] = v

    extra_list = sorted(extra_df['Course'].unique())
    return req_out, int_out, extra_df, extra_list


def calculate_credits(row, courses_dict):
    """
    Given a row where each course column is "grade tokens | credit" or "NR"/"CR | X"/"CR | PASS",
    returns a Series [completed, registered, remaining, total].
    """
    completed, registered, remaining = 0, 0, 0
    total = 0

    for course, credit in courses_dict.items():
        total += credit
        val = row.get(course, "")
        if isinstance(val, str):
            up = val.upper()
            if up.startswith("CR"):
                registered += credit
            elif up.startswith("NR"):
                remaining += credit
            else:
                parts = val.split("|")
                if len(parts) == 2:
                    right = parts[1].strip()
                    try:
                        num = int(right)
                        if num > 0:
                            completed += credit
                        else:
                            remaining += credit
                    except ValueError:
                        if right.upper() == "PASS":
                            pass
                        else:
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit

    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
    )


def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    """
    Exports the displayed DataFrames to a formatted Excel workbook with color
    coding: green for passed/CR, pink for failed/NR.
    """
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws_req = wb.active
    ws_req.title = "Required Courses"
    green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink  = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    yellow= PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_req.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                style = cell_color(str(val))
                if "#FFFACD" in style:
                    cell.fill = yellow
                elif "lightgreen" in style:
                    cell.fill = green
                else:
                    cell.fill = pink

    # Write Intensive sheet
    ws_int = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_int.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                style = cell_color(str(val))
                if "#FFFACD" in style:
                    cell.fill = yellow
                elif "lightgreen" in style:
                    cell.fill = green
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
