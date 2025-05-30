import streamlit as st

# Your existing grade order, with "CR" first so it's highest priority if you collapse later.
GRADE_ORDER = [
    "CR",
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-"
]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types (defaults to S.C.E and F.E.C, 
    but can be overridden in session state).
    """
    return st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if a grade token is in the comma-separated passing grades list.
    """
    try:
        passing = [g.strip().upper() for g in passing_grades_str.split(",")]
    except Exception:
        passing = []
    return grade.strip().upper() in passing

# Alias
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Applies background colors for cells showing one or more
    'GRADE | credit' entries (comma-separated):
      - If ANY entry starts with "CR", show pale yellow.
      - Else if ANY entry has credit > 0 or credit token "PASS", show light green.
      - Otherwise show pink.
    """
    if not isinstance(value, str):
        return ""

    # Split into individual entries like "F | 0" and "C- | 3"
    entries = [e.strip() for e in value.split(",") if e.strip()]

    # 1) If any entry is a current registration, color yellow
    for entry in entries:
        if entry.upper().startswith("CR"):
            return "background-color: #FFFACD"

    # 2) If any entry indicates passing credit (>0 or PASS), color green
    for entry in entries:
        parts = entry.split("|")
        if len(parts) == 2:
            right = parts[1].strip().upper()
            # numeric credits
            try:
                if int(right) > 0:
                    return "background-color: lightgreen"
            except ValueError:
                # PASS for zero-credit courses
                if right == "PASS":
                    return "background-color: lightgreen"

    # 3) Otherwise, not passed
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a full processed string (e.g. "F | 0, CR | 3"), picks the
    single highest-priority entry based on GRADE_ORDER (where CR is first),
    and returns it verbatim (including its credit part).
    """
    if not isinstance(value, str):
        return value

    # Split into entries
    entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in entries:
        if "|" in entry:
            g, c = entry.split("|", 1)
            parsed.append((g.strip().upper(), c.strip()))
        else:
            parsed.append((entry.strip().upper(), ""))

    # 1) Explicit CR check
    for grade_tok, cred in parsed:
        if grade_tok == "CR":
            return f"{grade_tok} | {cred}" if cred else "CR"

    # 2) Scan GRADE_ORDER
    for grade in GRADE_ORDER:
        for grade_tok, cred in parsed:
            if grade_tok == grade:
                return f"{grade_tok} | {cred}" if cred else grade

    # 3) Fallback to the very first entry
    if parsed:
        grade_tok, cred = parsed[0]
        return f"{grade_tok} | {cred}" if cred else grade_tok

    return ""
