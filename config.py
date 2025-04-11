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
    The grade is considered passing if its index (in GRADE_ORDER)
    is less than or equal to that of the passing_threshold.
    For example, if passing_threshold is "C", then any grade that appears
    earlier or at the same position in GRADE_ORDER (i.e. A+, A, A-, B+, B, B-, C+, C) is passing.
    """
    if grade not in GRADE_ORDER or passing_threshold not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(grade) <= GRADE_ORDER.index(passing_threshold)

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background color.
    - If the cell value starts with "CR", return light yellow (#FFFACD).
    - If the cell value contains a pipe ("|"), then the portion after the pipe
      is expected to be the awarded credits.
       • If that credit is "0", the cell is colored pink (failure).
       • Otherwise, the cell is colored light green.
    - In all other cases, default to pink.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith('CR'):
        return 'background-color: #FFFACD'
    if '|' in value:
        parts = value.split('|')
        if len(parts) > 1:
            credit_part = parts[1].strip()
            # If the course was not passed (credit 0), use pink; otherwise, light green.
            if credit_part == "0":
                return 'background-color: pink'
            else:
                return 'background-color: lightgreen'
    return 'background-color: pink'
