# config.py

import streamlit as st

# Include "CR" at the very front so it's highest priority
GRADE_ORDER = [
    "CR",
    "A+","A","A-",
    "B+","B","B-",
    "C+","C","C-",
    "D+","D","D-"
]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# Alias
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    if v.startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        try:
            num = int(right)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if right == "PASS":
                return "background-color: lightgreen"
            if right == "FAIL":
                return "background-color: pink"
    tokens = [t.strip() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a full cell string (e.g. "F | 0, CR | 3"), split into entries,
    then pick the entry whose grade (before '|') appears first in GRADE_ORDER.
    Return that grade and its credit part unchanged, e.g. "CR | 3".
    """
    if not isinstance(value, str):
        return value

    # Split on commas to get each "grade | credit" entry
    raw_entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in raw_entries:
        if "|" in entry:
            grade_part, cred_part = entry.split("|", 1)
            grade_token = grade_part.strip().upper()
            parsed.append((grade_token, cred_part.strip()))
        else:
            # If no '|', treat entire entry as a grade with empty credits
            parsed.append((entry.strip().upper(), ""))

    # Find the highest-priority grade present
    for grade in GRADE_ORDER:
        for tok, cred in parsed:
            if tok == grade:
                # Return exactly "GRADE | credit" (or just "GRADE" if no credit)
                return f"{tok} | {cred}" if cred else tok

    # Fallback to first entry
    if parsed:
        tok, cred = parsed[0]
        return f"{tok} | {cred}" if cred else tok

    return ""
