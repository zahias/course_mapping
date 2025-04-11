import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade(grade: str, passing_grades: list) -> bool:
    """
    Returns True if the provided grade (after trimming and in uppercase) 
    is found in the list passing_grades.
    """
    return grade in passing_grades

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the cell background color based on the processed grade cell value.
    - If the value starts with "CR", returns light yellow (#FFFACD).
    - Otherwise, the function splits the cell value by the pipe ("|") character.
      If the numeric part (after the pipe) is "0", the cell is considered failing and returns red.
      Otherwise, if a nonzero numeric value is found, returns light green.
    - If none of the above apply, returns a fallback pink.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    value_upper = value.upper()
    if value_upper.startswith("CR"):
        return "background-color: #FFFACD"  # Light yellow for currently registered
    if "|" in value:
        try:
            parts = value.split("|")
            credits_str = parts[1].strip()
            # If credits is "0", mark as failing (red); otherwise, passing (light green)
            if credits_str == "0":
                return "background-color: red"
            else:
                return "background-color: lightgreen"
        except Exception:
            pass
    return "background-color: pink"
