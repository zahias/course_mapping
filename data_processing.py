# data_processing.py

import pandas as pd

def read_progress_report(filepath):
    import streamlit as st

    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                req_cols = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not req_cols.issubset(df.columns):
                    st.error(f"Missing columns: {req_cols - set(df.columns)}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet found—attempting wide format.")
                df = pd.read_excel(xls)
                return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course','Grade','Year','Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV lacks expected columns—attempting wide format.")
                return transform_wide_format(df)
        else:
            st.error("Unsupported file type. Upload .xlsx, .xls, or .csv")
            return None
    except Exception as e:
        import streamlit as st
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    import streamlit as st

    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format missing 'STUDENT ID' or COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    df_m = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_m = df_m[df_m['CourseData'].notnull() & (df_m['CourseData']!='')]

    split = df_m['CourseData'].str.split('/', expand=True)
    if split.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE format.")
        return None

    df_m['Course'] = split[0].str.strip().str.upper()
    df_m['Semester_Year'] = split[1].str.strip()
    df_m['Grade'] = split[2].str.strip().str.upper()

    sem_y = df_m['Semester_Year'].str.split('-', expand=True)
    if sem_y.shape[1] < 2:
        st.error("Expected SEMESTER-YEAR format e.g. FALL-2016.")
        return None

    df_m['Semester'] = sem_y[0].str.title().str.strip()
    df_m['Year'] = sem_y[1].str.strip()
    df_m = df_m.rename(columns={'STUDENT ID':'ID','NAME':'NAME'})

    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(df_m.columns):
        st.error(f"Missing after transform: {req - set(df_m.columns)}")
        return None

    return df_m.loc[:, ['ID','NAME','Course','Grade','Year','Semester']].drop_duplicates()

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _, row in equiv_df.iterrows():
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
    df: raw progress DataFrame
    target_courses/intensive_courses: dict course->credits
    per_student_assignments: dict of {student_id:{assign_type:course}}
    equivalent_courses_mapping: dict eq_course->primary
    course_rules: dict course->list of {eff, passing_grades, credits}
    """
    import streamlit as st
    from config import get_allowed_assignment_types

    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # 1) numeric semester
    sem_map = {'Spring':1,'Summer':2,'Fall':3}
    df['SemValue'] = df['Year'].astype(int)*10 + df['Semester'].map(sem_map)

    # 2) apply equivalents
    df['Mapped Course'] = df['Course'].map(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) apply S.C.E./F.E.C.
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def apply_assign(r):
            sid, course = str(r['ID']), r['Course']
            mapped = r['Mapped Course']
            if sid in per_student_assignments:
                for t in allowed:
                    if per_student_assignments[sid].get(t) == course:
                        return t
            return mapped
        df['Mapped Course'] = df.apply(apply_assign, axis=1)

    # 4) determine pass based on rules
    def row_pass(r):
        course = r['Mapped Course']
        grade = str(r['Grade']).strip().upper()
        sv = r['SemValue']
        rules = course_rules.get(course, [])
        elig = [rule for rule in rules if rule['eff'] <= sv]
        if elig:
            rule = max(elig, key=lambda x: x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return grade in rule['passing_grades']

    df['PassedFlag'] = df.apply(row_pass, axis=1)

    # 5) split
    extra_df = df.loc[
        (~df['Mapped Course'].isin(target_courses))
      & (~df['Mapped Course'].isin(intensive_courses))
    ]
    targ_df = df[df['Mapped Course'].isin(target_courses)]
    inten_df = df[df['Mapped Course'].isin(intensive_courses)]

    # 6) pivot grades & flags
    pg = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna,map(str,x)))
    ).reset_index()
    pf = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    ipg = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna,map(str,x)))
    ).reset_index()
    ipf = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # 7) ensure columns
    for c in target_courses:
        if c not in pg: pg[c] = None
        if c not in pf: pf[c] = False
    for c in intensive_courses:
        if c not in ipg: ipg[c] = None
        if c not in ipf: ipf[c] = False

    # 8) merge into final cells
    def build_row(grades_row, flag_row, course_dict):
        cells = {}
        for course, cred in course_dict.items():
            gs = grades_row.get(course) or ''
            passed = bool(flag_row.get(course))
            if gs == '':
                cells[course] = 'NR'
            else:
                cells[course] = f"{gs} | {cred if passed else 0}"
        return cells

    req_out = pg[['ID','NAME']].copy()
    for i, row in pg.iterrows():
        cells = build_row(row, pf.iloc[i], target_courses)
        for k, v in cells.items():
            req_out.at[i, k] = v

    int_out = ipg[['ID','NAME']].copy()
    for i, row in ipg.iterrows():
        cells = build_row(row, ipf.iloc[i], intensive_courses)
        for k, v in cells.items():
            int_out.at[i, k] = v

    extra_list = sorted(extra_df['Course'].unique())
    return req_out, int_out, extra_df, extra_list

def calculate_credits(row, courses_dict):
    # ... your existing logic here ...
    import pandas as pd
    completed = registered = remaining = 0
    total = sum(courses_dict.values())
    for course, credit in courses_dict.items():
        val = row.get(course, '')
        if isinstance(val, str):
            up = val.upper()
            if up.startswith('CR'):
                registered += credit
            elif up.startswith('NR'):
                remaining += credit
            else:
                parts = val.split('|')
                if len(parts) == 2:
                    right = parts[1].strip()
                    try:
                        num = int(right)
                        if num > 0:
                            completed += credit
                        else:
                            remaining += credit
                    except:
                        if right.upper() != 'PASS':
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit
    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed','# Registered','# Remaining','Total Credits']
    )

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    # ... your existing Excel export logic here ...
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws1 = wb.active; ws1.title = "Required Courses"
    light_green = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')

    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row,1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            if r_idx==1:
                cell.font=Font(bold=True)
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD',end_color='FFFACD',fill_type='solid')
                else:
                    cell.fill = pink

    ws2 = wb.create_sheet("Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row,1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            if r_idx==1:
                cell.font=Font(bold=True)
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD',end_color='FFFACD',fill_type='solid')
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
