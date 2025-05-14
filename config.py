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
        return "background-color: #FFFACD"  # light yellow
    parts = value.split("|")
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
    # fallback: any counted grade in the left side?
    tokens = [t.strip().upper() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a full cell value—e.g. "F | 0, CR | 3" or "B+, C- | 3"—this:
      1. Splits on commas to get each attempt entry.
      2. Parses each entry into (grade_token, credit_part).
      3. Searches in GRADE_ORDER (with "CR" first) for the first matching grade_token.
      4. Returns "GRADE_TOKEN | credit_part".
    """
    if not isinstance(value, str):
        return value

    # Break into entries by comma that separate attempts
    entries = [e.strip() for e in value.split(",") if e.strip()]
    pairs = []
    for entry in entries:
        if "|" in entry:
            g, c = entry.split("|", 1)
            grade_token = g.strip().upper()
            credit_part = c.strip()
            pairs.append((grade_token, credit_part))
        else:
            # malformed entry; skip
            continue

    # Find the highest‐priority grade in your order
    for grade in GRADE_ORDER:
        for (gt, cp) in pairs:
            if gt == grade:
                return f"{gt} | {cp}"

    # Fallback: first entry
    if pairs:
        gt, cp = pairs[0]
        return f"{gt} | {cp}"

    # If nothing parsed, return original
    return value
