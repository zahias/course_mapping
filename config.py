# config.py

import streamlit as st

# Global grade order (highest → lowest). "CR" is first so that any in-progress supersedes past attempts.
GRADE_ORDER = [
    "CR",
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-"
]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise returns the default list.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is in the comma-separated list of passing grades.
    """
    try:
        allowed = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        allowed = []
    return grade.strip().upper() in allowed

# Alias for backward compatibility.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background.
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    if v.startswith("CR"):
        return "background-color: #FFFACD"  # light yellow for current registration
    parts = v.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        try:
            num = int(right)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if right == "PASS":
                return "background-color: lightgreen"
            if right == "FAIL":
                return "background-color: pink"
    # fallback: if any counted grade appears
    left_tokens = [t.strip() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in left_tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Collapse a full cell value (e.g. "F | 0, CR | 3, A- | 3") into a single "Primary | Credit":
    
      1. Split on commas to get each attempt entry.
      2. Trim and parse each entry into (grade_token, credit_part).
      3. **First**, look for any entry whose token is "CR" and return it.
      4. Otherwise, iterate through GRADE_ORDER in priority; if a token matches, return that entry.
      5. Fallback to the very first entry if nothing matched.
    """
    if not isinstance(value, str):
        return value

    entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in entries:
        if "|" in entry:
            g, c = entry.split("|", 1)
            grade_token = g.strip().upper()
            credit_part = c.strip()
            parsed.append((grade_token, credit_part))

    # 3) Highest priority: any "CR"
    for gt, cp in parsed:
        if gt == "CR":
            return f"{gt} | {cp}"

    # 4) Next: first grade found in GRADE_ORDER
    for grade in GRADE_ORDER:
        for gt, cp in parsed:
            if gt == grade:
                return f"{gt} | {cp}"

    # 5) Fallback: first parsed entry
    if parsed:
        gt, cp = parsed[0]
        return f"{gt} | {cp}"

    # If nothing parsed, return original
    return value
