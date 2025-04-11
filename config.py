import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_grades: list) -> bool:
    """
    Returns True if the provided grade (after stripping and uppercasing)
    is present in the list of passing grades (each element compared in uppercase).
    """
    return grade.strip().upper() in [g.strip().upper() for g in passing_grades]

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background color based on the grade value.
    - If the value starts with "CR", return light yellow (#FFFACD).
    - Otherwise, split the value by the pipe character ("|") to extract the grade part.
      If any token in that part is one of our valid grades (present in GRADE_ORDER), return light green;
      otherwise, return pink.
    """
    if not isinstance(value, str):
        return ''
    value_upper = value.upper()
    if value_upper.startswith('CR'):
        return 'background-color: #FFFACD'
    parts = value.split('|')
    if parts:
        grades_part = parts[0]
        grades_list = [g.strip() for g in grades_part.split(',') if g.strip()]
        if any(g in GRADE_ORDER for g in grades_list):
            return 'background-color: lightgreen'
    return 'background-color: pink'
