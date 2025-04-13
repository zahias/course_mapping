import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise, returns the default list.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is in the comma-separated list of passing grades.
    For example, if passing_grades_str is "A+,A,A-", then the function returns True
    if the uppercased, trimmed grade is found in that list.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility, provide an alias.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the cell background based on its processed value.
    
    Logic:
      - If the value starts with "CR", returns light yellow (#FFFACD) to indicate current registration.
      - Otherwise, it splits the value by the pipe ("|") and examines the right-hand side:
          • If numeric, a value > 0 means passed (light green); 0 means failed (pink).
          • If nonnumeric (e.g. "PASS" or "FAIL" for 0-credit courses), "PASS" yields light green and "FAIL" yields pink.
      - As a fallback, if any token in the left-hand side is in GRADE_ORDER, returns light green; otherwise, pink.
    """
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if value.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        try:
            num = int(right)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if right.upper() == "PASS":
                return "background-color: lightgreen"
            elif right.upper() == "FAIL":
                return "background-color: pink"
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(g in GRADE_ORDER for g in tokens):
        return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a processed full grade string (for example, "B+, A, C | 3" or "A, B | PASS"),
    this function extracts the primary grade based on GRADE_ORDER and preserves the earned credit.
    
    It splits the string at the pipe ("|"):
      - The left-hand side contains grade tokens (possibly multiple).
      - The right-hand side contains the earned credit (numeric or PASS/FAIL).
    The function returns a string in the format "PrimaryGrade | Credit".
    """
    if not isinstance(value, str):
        return value
    parts = value.split("|")
    if len(parts) < 2:
        return value
    grades_part = parts[0].strip()
    credit_part = parts[1].strip()
    if not grades_part:
        return ""
    tokens = [g.strip().upper() for g in grades_part.split(",") if g.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return f"{grade} | {credit_part}"
    return f"{tokens[0]} | {credit_part}" if tokens else ""
