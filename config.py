import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_threshold: str) -> bool:
    """
    Returns True if the given grade is considered passing 
    compared to the passing_threshold based on the global GRADE_ORDER.
    """
    if grade not in GRADE_ORDER or passing_threshold not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(grade) <= GRADE_ORDER.index(passing_threshold.upper())

def cell_color(value: str, passing_threshold: str) -> str:
    """
    Determines the cell background color based on the following rules:
    1) If the value starts with 'CR' (currently registered), return light yellow.
    2) Otherwise, if any grade in the cell (the portion before the '|') meets or exceeds 
       the passing_threshold per the GRADE_ORDER, return light green.
    3) Otherwise, return pink.
    """
    if not isinstance(value, str):
        return ''
    # Rule 1: Check for CR
    if value.upper().strip().startswith("CR"):
        return 'background-color: #FFFACD'
    
    # Extract the grade portion; assumes the format is "grade(s) | credits"
    parts = value.split('|')
    if parts:
        grades_part = parts[0].strip()
        if not grades_part:
            return 'background-color: pink'
        # Split into individual grades (assuming comma-separated if more than one)
        grades = [g.strip() for g in grades_part.split(',') if g.strip()]
        # Rule 2: Check if any grade meets the passing threshold
        for g in grades:
            if g in GRADE_ORDER and is_passing_grade(g, passing_threshold):
                return 'background-color: lightgreen'
    # Rule 3: Otherwise, return pink.
    return 'background-color: pink'
