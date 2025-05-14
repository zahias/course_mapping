import streamlit as st

# Global grade order (highest → lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

is_passing_grade = is_passing_grade_from_list  # alias for backward compatibility

def cell_color(value: str) -> str:
    if not isinstance(value, str):
        return ""
    v = value.strip()
    if v.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = v.split("|")
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
    From a detailed cell like "F | 0, CR | 3", picks CR first (if present),
    then the highest letter grade per GRADE_ORDER. Returns "Grade | Credit".
    """
    if not isinstance(value, str):
        return value

    # 1) Split into individual entries: ["F | 0", "CR | 3"]
    entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in entries:
        parts = [p.strip() for p in entry.split("|")]
        grade_tok = parts[0].upper()
        credit_tok = parts[1] if len(parts) > 1 else ""
        parsed.append((grade_tok, credit_tok))

    # 2) Define lookup order: CR first, then the normal grade hierarchy
    lookup_order = ["CR"] + GRADE_ORDER

    # 3) Find and return the first matching token
    for grade in lookup_order:
        for tok, cred in parsed:
            if tok == grade:
                return f"{tok} | {cred}"

    # 4) Fallback: return the very first entry
    tok, cred = parsed[0]
    return f"{tok} | {cred}"
