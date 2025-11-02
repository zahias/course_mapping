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
    Returns the list of assignment types.

    Priority:
      1) Per-Major override saved by Customize Courses:
         st.session_state[f"{selected_major}_allowed_assignment_types"]
      2) Global list (legacy support): st.session_state["allowed_assignment_types"]
      3) Default: ["S.C.E", "F.E.C"]
    """
    major = st.session_state.get("selected_major")
    if major:
        per_major = st.session_state.get(f"{major}_allowed_assignment_types")
        if isinstance(per_major, (list, tuple)) and len(per_major) > 0:
            return [str(x) for x in per_major if str(x).strip()]

    # Fallback to any global setting (if you ever set it elsewhere)
    global_list = st.session_state.get("allowed_assignment_types")
    if isinstance(global_list, (list, tuple)) and len(global_list) > 0:
        return [str(x) for x in global_list if str(x).strip()]

    # Default
    return ["S.C.E", "F.E.C"]

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

COMPLETION_COLOR_MAP = {
    "c": "background-color: #28a745",  # solid green for completed courses
    "cr": "background-color: #FFFACD",  # pale yellow for current registrations
    "nc": "background-color: #f8d7da",  # light red for not completed
}


def cell_color(value: str) -> str:
    """
    Applies background colors for cells showing one or more
    'GRADE | credit' entries (comma-separated).

    Collapsed completion toggle values ("c", "cr", "nc") map directly to their
    associated colors, while the legacy "GRADE | credit" strings retain the
    previous logic:
      - Any "CR" entry ⇒ pale yellow.
      - Any passing credit (>0 or "PASS") ⇒ solid green.
      - Otherwise ⇒ light red.
    """
    if not isinstance(value, str):
        return ""

    collapsed = value.strip().lower()
    if collapsed in COMPLETION_COLOR_MAP:
        return COMPLETION_COLOR_MAP[collapsed]

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
                    return COMPLETION_COLOR_MAP["c"]
            except ValueError:
                # PASS for zero-credit courses
                if right == "PASS":
                    return COMPLETION_COLOR_MAP["c"]

    # 3) Otherwise, not passed
    return COMPLETION_COLOR_MAP["nc"]

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
            credit = c.strip()
            parsed.append(
                {
                    "grade": g.strip().upper(),
                    "credit": credit,
                    "credit_upper": credit.upper(),
                    "original": entry,
                }
            )
        else:
            stripped = entry.strip()
            parsed.append(
                {
                    "grade": stripped.upper(),
                    "credit": "",
                    "credit_upper": "",
                    "original": stripped,
                }
            )

    # 1) Explicit CR check
    for entry in parsed:
        if entry["grade"] == "CR":
            return entry["original"]

    # 2) Scan GRADE_ORDER
    for grade in GRADE_ORDER:
        for entry in parsed:
            if entry["grade"] == grade:
                return entry["original"]

    # 3) Prefer any clearly completed attempt (credit > 0 or PASS)
    for entry in parsed:
        credit = entry["credit"].strip()
        if credit:
            try:
                if int(credit) > 0:
                    return entry["original"]
            except ValueError:
                if entry["credit_upper"] == "PASS":
                    return entry["original"]

    # 4) Fallback to the very first entry
    if parsed:
        return parsed[0]["original"]

    return ""
