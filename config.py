import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types that can be used.
    If the user has set a custom list via session state, that list is returned.
    Otherwise, it defaults to ["S.C.E", "F.E.C"].
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is among the allowed passing grades specified in the course configuration.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

is_passing_grade = is_passing_grade_from_list

def cell_color_obj(cell) -> str:
    """
    Expects cell to be a dict with keys "display" and "passed".
    Returns a CSS style string for the background color.
    - If the cell's display starts with "CR", returns light yellow (#FFFACD).
    - If the cell's passed flag is True, returns light green.
    - If the cell's passed flag is False, returns pink.
    - Otherwise, defaults to pink.
    """
    if not isinstance(cell, dict):
        return ''
    disp = cell.get("display", "").strip().upper()
    if disp.startswith("CR"):
        return 'background-color: #FFFACD'
    if cell.get("passed") is True:
        return 'background-color: lightgreen'
    elif cell.get("passed") is False:
        return 'background-color: pink'
    return 'background-color: pink'
