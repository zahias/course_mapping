# config.py

import streamlit as st

# Global grade order (highest → lowest).  
# We’ve prepended "CR" so that any "CR" beats even "A+" in primary‐grade view.
GRADE_ORDER = [
    "CR",
    "A+","A","A-",
    "B+","B","B-",
    "C+","C","C-",
    "D+","D","D-"
]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise returns the default list.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is in the comma-separated list of passing grades.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# Alias for backward compatibility.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background.
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    if v.startswith("CR"):
        return "background-color: #FFFACD"  # light yellow
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
    # fallback: any counted grade in the left side?
    tokens = [t.strip() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    From a full cell string like "F | 0, CR | 3" or "B+, C- | 3", picks the first token
    in GRADE_ORDER (now with "CR" highest), and re-appends the credit part.
    """
    if not isinstance(value, str):
        return value
    parts = value.split("|")
    if len(parts) < 2:
        return value  # nothing to collapse
    grades_part = parts[0].strip()
    credit_part = parts[1].strip()
    if not grades_part:
        return ""
    tokens = [g.strip().upper() for g in grades_part.split(",") if g.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return f"{grade} | {credit_part}"
    # fallback to first seen token
    return f"{tokens[0]} | {credit_part}" if tokens else ""
