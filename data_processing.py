import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

def read_progress_report(filepath):
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
                st.info("No 'Progress Report' sheet found – processing as wide format.")
                df = pd.read_excel(xls)
                df = transform_wide_format(df)
                if df is None:
                    st.error("Wide format transformation failed.")
                return df
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing expected columns – attempting wide format transformation.")
                df = transform_wide_format(df)
                return df
        else:
            st.error("Unsupported file format. Please upload an Excel or CSV file.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(col.startswith('COURSE') for col in df.columns):
        st.error("Wide format file missing 'STUDENT ID' or COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name="Course_Column", value_name="CourseData")
    df_melted = df_melted[df_melted["CourseData"].notnull() & (df_melted["CourseData"] != "")]
    split_cols = df_melted["CourseData"].str.split("/", expand=True)
    if split_cols.shape[1] < 3:
        st.error("Parsing error: Expected format COURSECODE/SEMESTER-YEAR/GRADE.")
        return None
    df_melted["Course"] = split_cols[0].str.strip().str.upper()
    df_melted["Semester_Year"] = split_cols[1].str.strip()
    df_melted["Grade"] = split_cols[2].str.strip().str.upper()
    sem_year_split = df_melted["Semester_Year"].str.split("-", expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized. Expected e.g. FALL-2016.")
        return None
    df_melted["Semester"] = sem_year_split[0].str.strip().str.title()
    df_melted["Year"] = sem_year_split[1].str.strip()
    df_melted = df_melted.rename(columns={"STUDENT ID": "ID", "NAME": "NAME"})
    req_cols = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
    if not req_cols.issubset(df_melted.columns):
        st.error(f"Missing columns after transformation: {req_cols - set(df_melted.columns)}")
        return None
    return df_melted[list(req_cols)].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for idx, row in equivalent_courses_df.iterrows():
        primary = row["Course"].strip().upper()
        equivalents = [x.strip().upper() for x in str(row["Equivalent"]).split(",")]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping

def process_progress_report(df, target_courses, intensive_courses,
                            per_student_assignments=None,
                            equivalent_courses_mapping=None):
    # 1) Prepare and map equivalents
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df = df.copy()
    df["Mapped Course"] = df["Course"].apply(
        lambda x: equivalent_courses_mapping.get(x, x)
    )

    # 2) Apply per-student S.C.E. / F.E.C.
    if per_student_assignments:
        allowed_types = get_allowed_assignment_types()
        def map_assignment(row):
            sid = str(row["ID"])
            course = row["Course"]
            mapped = row["Mapped Course"]
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for atype in allowed_types:
                    if assigns.get(atype) == course:
                        return atype
            return mapped
        df["Mapped Course"] = df.apply(map_assignment, axis=1)

    # 3) Compute a semester ordinal to support date‐ranges if you ever extend that
    sem_order = {"Fall":0, "Spring":1, "Summer":2}
    df["SemOrd"] = df.apply(
        lambda r: sem_order.get(r["Semester"], 0) + int(r["Year"])*3,
        axis=1
    )

    # 4) **New** — row‐wise 'ProcessedValue' using your existing determine_course_value:
    #    merge the two config dicts so determine_course_value sees both target & intensive
    course_info = {**target_courses, **intensive_courses}
    df["ProcessedValue"] = df.apply(
        lambda r: determine_course_value(
            r["Grade"],
            r["Mapped Course"],
            course_info
        ), axis=1
    )

    # 5) Split into Required, Intensive, Extra
    extra_courses_df = df[
        (~df["Mapped Course"].isin(target_courses.keys())) &
        (~df["Mapped Course"].isin(intensive_courses.keys()))
    ]
    target_df    = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]

    # 6) Pivot **on** our new 'ProcessedValue'
    pivot_df = target_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    intensive_pivot_df = intensive_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    # 7) Ensure every column appears
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None

    result_df = pivot_df[["ID", "NAME"] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[["ID", "NAME"] + list(intensive_courses.keys())]

    # 8) Remove assigned from extras (vectorized)
    if per_student_assignments:
        assigned = {
            (sid, crs)
            for sid, assigns in per_student_assignments.items()
            for crs in assigns.values()
        }
        extra_courses_df = extra_courses_df.copy()
        extra_courses_df["_key"] = list(zip(
            extra_courses_df["ID"].astype(str),
            extra_courses_df["Course"]
        ))
        extra_courses_df = extra_courses_df[
            ~extra_courses_df["_key"].isin(assigned)
        ].drop(columns=["_key"])

    extra_courses_list = sorted(extra_courses_df["Course"].unique())
    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    """
    Unchanged — gives 'NR', 'CR | X', 'Tokens | X', or 'Tokens | PASS/FAIL'.
    """
    info = courses_dict.get(course, {"Credits":0,"PassingGrades":""})
    credits = info["Credits"]
    passing = info["PassingGrades"]
    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}" if credits>0 else "CR | PASS"
    tokens = [g.strip().upper() for g in grade.split(", ") if g.strip()]
    allowed = [x.strip().upper() for x in passing.split(",")]
    passed = any(t in allowed for t in tokens)
    all_toks = ", ".join(tokens)
    if credits>0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def calculate_credits(row, courses_dict):
    """
    Unchanged — counts '# of Credits Completed', etc.
    """
    completed, registered, remaining = 0, 0, 0
    total = 0
    for course, info in courses_dict.items():
        cred = info["Credits"]
        total += cred
        val = row.get(course, "")
        if isinstance(val, str):
            u = val.upper()
            if u.startswith("CR"):
                registered += cred
            elif u.startswith("NR"):
                remaining += cred
            else:
                parts = val.split("|")
                if len(parts)==2:
                    right = parts[1].strip()
                    try:
                        n = int(right)
                        if n>0:
                            completed += cred
                        else:
                            remaining += cred
                    except:
                        if right.upper()!="PASS":
                            remaining += cred
        else:
            remaining += cred
    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed","# Registered","# Remaining","Total Credits"]
    )

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
    pink        = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")

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
