# config.py
# Central config helpers used across the app.

from __future__ import annotations
from typing import List, Iterable, Optional
import streamlit as st

# -----------------------------
# Grades & display helpers
# -----------------------------

# Order used anywhere you need to sort or compare letter grades.
GRADE_ORDER: List[str] = [
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-",
    "P",            # Pass (if used)
    "CR",           # Credit/Registered markers sometimes appear
    "NR",           # Not Registered
    "F",            # Fail
    "NP",           # Not Pass (if used)
    "W",            # Withdraw
    "I",            # Incomplete
]

def is_passing_grade(grade: str, passing_grades_csv: str) -> bool:
    """
    Returns True if `grade` (e.g., 'B+') is contained in the comma-separated
    list `passing_grades_csv` (e.g., 'A+,A,A-,B+,B,B-').
    Matching is case-insensitive and trims whitespace.
    """
    if not grade or not passing_grades_csv:
        return False
    allowed = {g.strip().upper() for g in passing_grades_csv.split(",") if g.strip()}
    return grade.strip().upper() in allowed

def extract_primary_grade_from_full_value(val: object) -> object:
    """
    Collapses a full cell like 'A, A- | 3' into 'A | 3'.
    Leaves 'NR' or '' (failed) as-is. Pass-through for non-str values.
    """
    if not isinstance(val, str):
        return val
    s = val.strip()
    if s == "" or s.upper() == "NR":
        return s
    if "|" in s:
        left, right = s.split("|", 1)
        first_grade = left.split(",")[0].strip()
        return f"{first_grade} | {right.strip()}"
    # values like 'CR' (no pipe) – show as-is
    return s

def cell_color(value: object) -> str:
    """
    Returns a CSS style string for DataFrame .style.applymap() based on cell value:
      - lightgreen: passed / positive credits / PASS
      - #FFFACD   : registered markers (NR or CR) / in-progress
      - pink      : failed or zero credits
    This matches the legend used in View Reports.
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()

    # Collapsed view 'c' (Show Completed/Not Completed toggle)
    if v == "C":
        return "background-color: lightgreen"

    # Explicit markers for registration/in-progress
    if v == "NR" or v.startswith("CR"):
        return "background-color: #FFFACD"

    # Full-form values like 'A | 3', 'B | 0', 'PASS | PASS', 'F | 0'
    if "|" in v:
        _, right = v.split("|", 1)
        r = right.strip()
        # Numeric credits
        try:
            if int(r) > 0:
                return "background-color: lightgreen"
            else:
                return "background-color: pink"
        except ValueError:
            # PASS / FAIL textual right-sides
            if r == "PASS":
                return "background-color: lightgreen"
            if r == "FAIL":
                return "background-color: pink"
            # Fallback
            return ""
    # Unknown string – no styling
    return ""

# -----------------------------
# Assignment Types (S.C.E., F.E.C., etc.)
# -----------------------------

# Default (used only if no per-Major override is present).
_DEFAULT_ALLOWED_ASSIGNMENT_TYPES: List[str] = ["S.C.E", "F.E.C"]

def get_allowed_assignment_types() -> List[str]:
    """
    Returns the list of assignment type slots that are *currently active*.

    IMPORTANT:
    - If a Major is selected and Customize Courses saved an override in
      st.session_state[f"{major}_allowed_assignment_types"], that list is returned.
    - Otherwise we return the default list.

    This makes all pages (including UI helpers) automatically reflect the
    customization without changing their code.
    """
    major = st.session_state.get("selected_major")
    if major:
        override = st.session_state.get(f"{major}_allowed_assignment_types")
        if isinstance(override, (list, tuple)) and len(override) > 0:
            # Return exactly what the user configured (preserve punctuation/case).
            # Downstream logic (e.g., processors) can normalize if needed.
            return [str(x) for x in override if str(x).strip()]

    # Fallback to app default
    return list(_DEFAULT_ALLOWED_ASSIGNMENT_TYPES)
