import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types, extract_primary_grade_from_full_value, cell_color
from logging_utils import log_action

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

def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    df = df.copy()

    # 1) Apply equivalent‐course mapping
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 2) Apply S.C.E./F.E.C. overrides
    if per_student_assignments:
        allowed_types = get_allowed_assignment_types()

        def map_assignment(row):
            sid = str(row["ID"])
            course = row["Course"]
            mapped = row["Mapped Course"]
            if sid in per_student_assignments:
                for atype in allowed_types:
                    if per_student_assignments[sid].get(atype) == course:
                        return atype
            return mapped

        df["Mapped Course"] = df.apply(map_assignment, axis=1)

    # 3) Compute a per‐row ProcessedValue (so blank→"CR | X" is captured)
    df["ProcessedValue"] = df.apply(
        lambda row: determine_course_value(
            row["Grade"],
            row["Mapped Course"],
            target_courses if row["Mapped Course"] in target_courses else intensive_courses
        ),
        axis=1
    )

    # 4) Split into required/intensive/extra based on Mapped Course
    extra_courses_df = df[
        (~df["Mapped Course"].isin(target_courses.keys())) &
        (~df["Mapped Course"].isin(intensive_courses.keys()))
    ]
    target_df = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]

    # 5) Pivot on ProcessedValue
    pivot_df = target_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda x: ", ".join(x)
    ).reset_index()
    intensive_pivot_df = intensive_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda x: ", ".join(x)
    ).reset_index()

    # 6) Ensure all columns exist
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None

    result_df = pivot_df[["ID", "NAME"] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[["ID", "NAME"] + list(intensive_courses.keys())]

    # 7) Remove already‐assigned extra rows
    if per_student_assignments:
        assigned = set(
            (sid, crs)
            for sid, asgs in per_student_assignments.items()
            for crs in asgs.values()
        )
        extra_courses_df = extra_courses_df.copy()
        extra_courses_df["_key"] = list(zip(extra_courses_df["ID"].astype(str), extra_courses_df["Course"]))
        extra_courses_df = extra_courses_df[~extra_courses_df["_key"].isin(assigned)].drop(columns=["_key"])

    extra_courses_list = sorted(extra_courses_df["Course"].unique())

    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    """
    Processes a course grade:
    - blank → "CR | credits" (or "CR | PASS" if zero-credit)
    - nan → "NR"
    - otherwise → "<all tokens> | <credits or 0 or PASS/FAIL>"
    """
    info = courses_dict[course]
    credits = info["Credits"]
    passing_grades_str = info["PassingGrades"]

    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"

    tokens = [g.strip().upper() for g in grade.split(", ") if g.strip()]
    all_tokens = ", ".join(tokens)
    allowed = [x.strip().upper() for x in passing_grades_str.split(",")]
    passed = any(g in allowed for g in tokens)

    if credits > 0:
        return f"{all_tokens} | {credits}" if passed else f"{all_tokens} | 0"
    else:
        return f"{all_tokens} | PASS" if passed else f"{all_tokens} | FAIL"

def calculate_credits(row, courses_dict):
    completed, registered, remaining = 0, 0, 0
    total = 0
    for course, info in courses_dict.items():
        credit = info["Credits"]
        total += credit
        val = row.get(course, "")
        if isinstance(val, str):
            v = val.upper()
            if v.startswith("CR"):
                registered += credit
            elif v.startswith("NR"):
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
                        if right.upper() != "PASS":
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit
    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
    )
