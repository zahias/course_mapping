import streamlit as st

# Global grade order is still defined for reference; it is not used for passing comparisons anymore.
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def cell_color(value: str) -> str:
    """
    Determines the cell background color based on the computed course value string.
    The expected format is either:
      - "CR | {credits}" for currently registered courses,
      - "{grades} | {credits}" where {credits} is the awarded credits.
    If credits are greater than 0, the cell is light green.
    If credits equal 0, it is red.
    "CR" cells are light yellow.
    """
    if not isinstance(value, str):
        return ''
    value_upper = value.upper()
    if value_upper.startswith('CR'):
        return 'background-color: #FFFACD'  # Light yellow
    if '|' in value:
        parts = value.split('|')
        credit_part = parts[1].strip()
        try:
            credit_val = float(credit_part)
            if credit_val > 0:
                return 'background-color: lightgreen'
            else:
                return 'background-color: red'
        except Exception:
            return 'background-color: pink'
    return 'background-color: pink'
