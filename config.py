import streamlit as st

# Global grade order remains available (if needed elsewhere)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types that can be used.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is one of the acceptable passing grades (defined in the course configuration).
    
    Parameters:
      - grade: The student's grade token (e.g., "B+").
      - passing_grades_str: A comma-separated string of passing grades (e.g., "A+,A,A-").
    
    Returns:
      - True if grade (uppercased and trimmed) is in the list.
      - False otherwise.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility, export an alias.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style for the cell background based on the processed grade value.
    Expects value in the format:
        "grade tokens | credits | marker"
    Where marker is either "PASS" or "FAIL". (Cells starting with "CR" are for currently registered.)
    
    Rules:
      - If the value starts with "CR": return light yellow (#FFFACD).
      - Otherwise, split the value by the pipe ("|") and inspect the third component:
          * If it equals "PASS", return light green.
          * If it equals "FAIL" (or anything else), return pink.
    """
    if not isinstance(value, str):
        return ''
    
    value = value.strip()
    if value.upper().startswith("CR"):
        return 'background-color: #FFFACD'
    
    parts = value.split("|")
    if len(parts) >= 3:
        marker = parts[2].strip().upper()
        if marker == "PASS":
            return 'background-color: lightgreen'
        else:
            return 'background-color: pink'
    
    return 'background-color: pink'
