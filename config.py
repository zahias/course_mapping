import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_threshold: str) -> bool:
    """
    Determines if a single grade meets the passing threshold.
    When a threshold is given as a single grade, a grade is passing if its index in GRADE_ORDER is less
    than or equal to that of the passing_threshold.
    """
    if grade not in GRADE_ORDER or passing_threshold not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(grade) <= GRADE_ORDER.index(passing_threshold)

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for a cell based on its grade value.
    
    Logic:
      - If the value starts with "CR", return light yellow (indicating "Currently Registered").
      - Otherwise, split the value using the pipe (|) character.
        • If the credit part (after the "|") is greater than 0, return light green (indicating passed).
        • If it is 0, return pink (indicating not passed).
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split("|")
    if len(parts) == 2:
        try:
            credit = float(parts[1].strip())
        except Exception:
            credit = 0
        if credit > 0:
            return "background-color: lightgreen"
        else:
            return "background-color: pink"
    return "background-color: pink"
