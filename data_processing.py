import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def read_progress_report(filepath):
    # ... your existing read logic (unchanged) ...
    # Make sure you still have your read_progress_report and transform_wide_format functions here
    raise NotImplementedError("Use your existing code.")

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _, r in equiv_df.iterrows():
        prim = r['Course'].strip().upper()
        eqs = [c.strip().upper() for c in str(r['Equivalent']).split(',')]
        for e in eqs:
            mapping[e] = prim
    return mapping

def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None,
    course_rules=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # 1) compute numeric semester value
    sem_map = {'Spring':1,'Summer':2,'Fall':3}
    df['SemValue'] = df['Year'].astype(int)*10 + df['Semester'].map(sem_map)

    # 2) map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) apply S.C.E/F.E.C assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID']); c = r['Course']; m = r['Mapped Course']
            if sid in per_student_assignments:
                for t in allowed:
                    if per_student_assignments[sid].get(t)==c:
                        return t
            return m
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 4) determine PassedFlag based on effective rules
    def passed(r):
        course = r['Mapped Course']
        g = str(r['Grade']).strip().upper()
        sv = r['SemValue']
        rules = course_rules.get(course, [])
        # find rule with max eff <= sv
        applicable = [rule for rule in rules if rule['eff']<=sv]
        if applicable:
            rule = max(applicable, key=lambda x:x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return g in rule['passing_grades']

    df['PassedFlag'] = df.apply(passed, axis=1)

    # 5) split into extra/target/intensive
    extra = df[
        ~df['Mapped Course'].isin(target_courses) &
        ~df['Mapped Course'].isin(intensive_courses)
    ]
    targ = df[df['Mapped Course'].isin(target_courses)]
    inten = df[df['Mapped Course'].isin(intensive_courses)]

    # 6) pivot grades & flags
    pg = targ.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()
    pp = targ.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    ipg = inten.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()
    ipp = inten.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # 7) ensure all columns present
    for c in target_courses:
        if c not in pg: pg[c]=None
        if c not in pp: pp[c]=False
    for c in intensive_courses:
        if c not in ipg: ipg[c]=None
        if c not in ipp: ipp[c]=False

    # 8) build final DataFrames: "grade tokens | credits or 0"
    def merge_row(g_row, f_row, course_dict):
        out={}
        for course, cred in course_dict.items():
            gs = g_row.get(course) or ''
            ok = bool(f_row.get(course))
            if gs=='':
                cell = 'NR'
            else:
                cell = f"{gs} | {cred if ok else 0}"
            out[course] = cell
        return out

    req_out = pg[['ID','NAME']].copy()
    for i, r in pg.iterrows():
        flags = pp.iloc[i]
        rowmap = merge_row(r, flags, target_courses)
        for k,v in rowmap.items():
            req_out.at[i,k] = v

    int_out = ipg[['ID','NAME']].copy()
    for i, r in ipg.iterrows():
        flags = ipp.iloc[i]
        rowmap = merge_row(r, flags, intensive_courses)
        for k,v in rowmap.items():
            int_out.at[i,k] = v

    extra_list = sorted(extra['Course'].unique())
    return req_out, int_out, extra, extra_list



def calculate_credits(row, courses_dict):
    completed, registered, remaining = 0, 0, 0
    total = 0
    for course, info in courses_dict.items():
        credit = info["Credits"]
        total += credit
        value = row.get(course, "")
        if isinstance(value, str):
            up_val = value.upper()
            if up_val.startswith("CR"):
                registered += credit
            elif up_val.startswith("NR"):
                remaining += credit
            else:
                parts = value.split("|")
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
                            # 0-credit passed; no credit to add, but considered passed
                            pass
                        else:
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit
    return pd.Series([completed, registered, remaining, total],
                     index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"])

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color
    output = io.BytesIO()
    workbook = Workbook()
    ws_req = workbook.active
    ws_req.title = "Required Courses"
    light_green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_req.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                if value == "c":
                    cell.fill = light_green
                elif value == "":
                    cell.fill = pink
                else:
                    style = cell_color(str(value))
                    if "lightgreen" in style:
                        cell.fill = light_green
                    elif "#FFFACD" in style:
                        cell.fill = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")
                    else:
                        cell.fill = pink
    ws_int = workbook.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_int.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                if value == "c":
                    cell.fill = light_green
                elif value == "":
                    cell.fill = pink
                else:
                    style = cell_color(str(value))
                    if "lightgreen" in style:
                        cell.fill = light_green
                    elif "#FFFACD" in style:
                        cell.fill = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")
                    else:
                        cell.fill = pink
    workbook.save(output)
    output.seek(0)
    return output
