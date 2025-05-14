import streamlit as st

# Global grade order (highest → lowest).  CR isn’t a “grade” per se, so we don’t add it here.
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise defaults to ['S.C.E', 'F.E.C'].
    """
    return st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is in the comma-separated list of passing grades.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# Alias for backward compatibility
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background based on the stored value.
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    # Currently Registered
    if v.startswith("CR"):
        return "background-color: #FFFACD"
    parts = v.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        # numeric credit
        try:
            num = int(right)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if right == "PASS":
                return "background-color: lightgreen"
            elif right == "FAIL":
                return "background-color: pink"
    # any counted letter grade?
    left_tokens = [g.strip() for g in parts[0].split(",") if g.strip()]
    if any(tok in GRADE_ORDER for tok in left_tokens):
        return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a full cell value like "F | 0, CR | 3" or "B+, C | 3":
    
    1) Split into grade-tokens and credit.
    2) If any token is "CR", return "CR | <credit>".
    3) Else, return the highest-priority letter grade from GRADE_ORDER.
    4) If none match, fall back to the first token.
    """
    if not isinstance(value, str):
        return value
    parts = value.split("|")
    # If there’s no credit piece, just return as-is
    if len(parts) < 2:
        return value
    grades_part = parts[0].strip()
    credit_part = parts[1].strip()
    if not grades_part:
        return ""
    # Build a clean list of tokens: e.g. ["F", "CR"]
    tokens = [g.strip().upper() for g in grades_part.split(",") if g.strip()]
    # 1) CR wins
    if "CR" in tokens:
        return f"CR | {credit_part}"
    # 2) Highest letter grade from GRADE_ORDER
    for grade in GRADE_ORDER:
        if grade in tokens:
            return f"{grade} | {credit_part}"
    # 3) Fallback to first token
    return f"{tokens[0]} | {credit_part}"
