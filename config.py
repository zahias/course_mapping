import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_threshold: str) -> bool:
    """
    Returns True if the grade is considered passing based on the configured grade order.
    The grade is considered passing if its position in GRADE_ORDER is less than or equal to that of the passing_threshold.
    """
    if grade not in GRADE_ORDER or passing_threshold not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(grade) <= GRADE_ORDER.index(passing_threshold)

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for background color based on grade information in the cell.
    - If the cell value starts with 'CR', returns light yellow (#FFFACD).
    - Otherwise, if the portion before a "|" contains any valid grade from GRADE_ORDER, returns light green;
      if no valid grade is present, returns pink.
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
