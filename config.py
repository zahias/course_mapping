import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_threshold: str) -> bool:
    """
    Determines if a single grade is passing.
    The grade is considered passing if its rank (index in GRADE_ORDER)
    is less than or equal to that of the passing_threshold.
    For example, if passing_threshold is "C", then any grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"] passes.
    """
    if grade not in GRADE_ORDER or passing_threshold not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(grade) <= GRADE_ORDER.index(passing_threshold)

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
