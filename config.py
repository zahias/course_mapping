import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_grades: list) -> bool:
    """
    Returns True if 'grade' (assumed to be uppercase and trimmed)
    is in the list 'passing_grades'.
    """
    return grade in passing_grades

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the cell background based on the cell's value:
      - If the value starts with "CR", returns light yellow (#FFFACD).
      - Otherwise, splits the value by '|' to extract the grade portion.
        If any token (after trimming) is one of the valid grades (present in GRADE_ORDER), returns light green;
        otherwise, returns pink.
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
