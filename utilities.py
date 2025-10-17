# utilities.py

import pandas as pd
from openpyxl.styles import PatternFill, Font
from typing import List, Dict, Tuple, Optional

# ---------- General helpers ----------

def safe_strip_upper(x: str) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return str(x).strip().upper()

def parse_requirements(req_str: str) -> List[str]:
    """
    Split a requisite string on commas, normalize spaces, and drop 'N/A' or blanks.
    """
    if req_str is None or (isinstance(req_str, float) and pd.isna(req_str)):
        return []
    s = str(req_str).strip()
    if s == "" or s.upper() == "N/A":
        return []
    return [token.strip() for token in s.split(",") if token.strip()]

def get_student_total_credits(student_row: dict) -> int:
    """
    Total credits used for standing and eligibility:
    (# of Credits Completed) + (# Registered)
    """
    completed = student_row.get("# of Credits Completed", 0)
    registered = student_row.get("# Registered", 0)
    try:
        completed = int(completed) if pd.notna(completed) else 0
    except Exception:
        completed = 0
    try:
        registered = int(registered) if pd.notna(registered) else 0
    except Exception:
        registered = 0
    return completed + registered

def get_student_standing(total_credits: int) -> str:
    """
    Sophomore <30, Junior 30-59, Senior >=60.
    """
    if total_credits >= 60:
        return "Senior"
    if total_credits >= 30:
        return "Junior"
    return "Sophomore"

def check_course_completed(student_row: dict, course_code: str) -> bool:
    """
    A course is considered completed if its cell in the progress wide table equals 'c' (case-insensitive).
    """
    val = safe_strip_upper(student_row.get(course_code, ""))
    return val == "C"

def check_course_registered(student_row: dict, course_code: str) -> bool:
    """
    A course is considered currently registered if its cell equals 'NR' (case-insensitive).
    """
    val = safe_strip_upper(student_row.get(course_code, ""))
    return val == "NR"

def is_course_offered(courses_df: pd.DataFrame, course_code: str) -> bool:
    if courses_df is None or courses_df.empty:
        return False
    row = courses_df.loc[courses_df["Course Code"] == course_code]
    if row.empty:
        return False
    offered = safe_strip_upper(row.iloc[0].get("Offered", "No"))
    return offered == "YES"

def build_requisites_str(course_row: pd.Series) -> str:
    pieces = []
    for col, label in [("Prerequisite", "Prereq"), ("Concurrent", "Conc"), ("Corequisite", "Coreq")]:
        val = course_row.get(col, "")
        toks = parse_requirements(val)
        if toks:
            pieces.append(f"{label}: {', '.join(toks)}")
    return "; ".join(pieces) if pieces else "None"

# ---------- Eligibility ----------

def _standing_ok(needed: str, total_credits: int) -> Tuple[bool, Optional[str]]:
    """
    Check 'Junior standing' or 'Senior standing' need against total credits.
    Returns (ok, reason_if_not_ok).
    """
    need_upper = safe_strip_upper(needed)
    if need_upper == "JUNIOR STANDING":
        if get_student_standing(total_credits) in ("Junior", "Senior"):
            return True, None
        return False, "Junior standing not met."
    if need_upper == "SENIOR STANDING":
        if get_student_standing(total_credits) == "Senior":
            return True, None
        return False, "Senior standing not met."
    return True, None

def check_eligibility(
    student_row: dict,
    course_code: str,
    advised_courses: List[str],
    courses_df: pd.DataFrame
) -> Tuple[str, str]:
    """
    Returns ('Eligible'|'Not Eligible'|'Completed'|'Registered', justification)
    Logic:
      - Not eligible if not offered
      - Prereqs must be completed; 'Junior/Senior standing' use Completed+Registered sum
      - Concurrent must be completed OR advised
      - Coreq must be advised
      - Course not already completed or registered
    """
    # If not found
    row = courses_df.loc[courses_df["Course Code"] == course_code]
    if row.empty:
        return "Not Eligible", "Course not found."

    course = row.iloc[0]
    reasons = []

    # Completed/Registered checks
    if check_course_completed(student_row, course_code):
        return "Completed", "Course already completed."
    if check_course_registered(student_row, course_code):
        return "Registered", "Course currently registered."

    # Offered
    if not is_course_offered(courses_df, course_code):
        reasons.append("Course not offered this semester.")

    total_credits = get_student_total_credits(student_row)

    # Prerequisites
    for req in parse_requirements(course.get("Prerequisite", "")):
        ok, reason = _standing_ok(req, total_credits)
        if not ok:
            reasons.append(reason)
            continue
        # If not a standing token, must be completed as a course
        if reason is None and req.upper() not in ("JUNIOR STANDING", "SENIOR STANDING"):
            if not check_course_completed(student_row, req):
                reasons.append(f"Prerequisite {req} not completed.")

    # Concurrent: must be completed or advised
    for conc in parse_requirements(course.get("Concurrent", "")):
        if not (check_course_completed(student_row, conc) or conc in advised_courses):
            reasons.append(f"Concurrent requirement {conc} not met (complete or advise).")

    # Coreq: must be advised simultaneously
    for coreq in parse_requirements(course.get("Corequisite", "")):
        if coreq not in advised_courses:
            reasons.append(f"Corequisite {coreq} not met (must advise together).")

    if reasons:
        return "Not Eligible", "; ".join(dict.fromkeys(reasons))  # dedupe in order
    return "Eligible", "All requirements met."

# ---------- Styling ----------

def style_df(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """
    Color rows by Action/Status:
      - Completed: gray
      - Registered: lightsteelblue
      - Advised: lightgreen
      - Optional: light yellow
      - Eligible (not chosen): pale green
      - Not Eligible: light coral
    """
    def _row_style(row):
        act = row.get("Action", "")
        status = row.get("Eligibility Status", "")
        if "Completed" in act:
            return ["background-color: #D3D3D3"] * len(row)
        if "Registered" in act:
            return ["background-color: #B0C4DE"] * len(row)
        if "Advised" in act:
            return ["background-color: #90EE90"] * len(row)
        if "Optional" in act:
            return ["background-color: #FFFACD"] * len(row)
        if status == "Eligible":
            return ["background-color: #E0FFE0"] * len(row)
        if status == "Not Eligible":
            return ["background-color: #F08080"] * len(row)
        return [""] * len(row)

    widths = {
        "Course Code": "90px",
        "Type": "90px",
        "Requisites": "300px",
        "Eligibility Status": "130px",
        "Justification": "320px",
        "Offered": "70px",
        "Action": "160px",
    }

    styler = df.style.apply(_row_style, axis=1)
    for col, w in widths.items():
        if col in df.columns:
            styler = styler.set_properties(subset=[col], **{"width": w})
    styler = styler.set_table_styles([{
        "selector": "th",
        "props": [("text-align", "left"), ("font-weight", "bold")]
    }])
    styler = styler.set_properties(**{"text-align": "left"})
    return styler

# ---------- Merge helpers ----------

REQUIRED_CONFIG_COLS = {
    "Course Code", "Credits", "Type", "Prerequisite", "Concurrent", "Corequisite"
}
MIN_TABLE_COLS = {"Course Code", "Course Name", "Credits", "Offered"}

def merge_courses_config_and_table(config_df: pd.DataFrame, table_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge a required courses-config (rules) with an optional raw courses table (names, offered).
    Prefers values from config_df where overlapping, except 'Course Name' which comes from the table if present.
    """
    if not REQUIRED_CONFIG_COLS.issubset(config_df.columns):
        missing = REQUIRED_CONFIG_COLS - set(config_df.columns)
        raise ValueError(f"Courses configuration missing columns: {missing}")

    merged = config_df.copy()

    if table_df is not None and not table_df.empty:
        if "Course Code" not in table_df.columns:
            raise ValueError("Courses table missing 'Course Code'.")
        # Keep only useful columns from the table if they exist
        keep_cols = [c for c in ["Course Code", "Course Name", "Credits", "Offered"] if c in table_df.columns]
        table_trim = table_df[keep_cols].copy()
        merged = pd.merge(table_trim, merged, on="Course Code", how="outer", suffixes=("_table", ""))

        # Credits: prefer config if present, else from table
        if "Credits_table" in merged.columns:
            merged["Credits"] = merged.apply(
                lambda r: r["Credits"] if pd.notna(r.get("Credits")) else r.get("Credits_table"),
                axis=1
            )
            merged.drop(columns=["Credits_table"], inplace=True)

        # Offered default to "Yes" unless table said otherwise
        if "Offered" not in merged.columns:
            merged["Offered"] = "Yes"
        merged["Offered"] = merged["Offered"].fillna("Yes")

        # Type default to "Required" if missing
        if "Type" not in merged.columns:
            merged["Type"] = "Required"
        merged["Type"] = merged["Type"].fillna("Required")
    else:
        # No separate table → ensure minimum projected columns
        if "Course Name" not in merged.columns:
            merged["Course Name"] = merged["Course Code"]
        if "Offered" not in merged.columns:
            merged["Offered"] = "Yes"
        merged["Type"] = merged["Type"].fillna("Required")

    # Normalize string columns
    for c in ["Prerequisite", "Concurrent", "Corequisite", "Offered", "Type", "Course Name"]:
        if c in merged.columns:
            merged[c] = merged[c].apply(lambda v: "" if pd.isna(v) else v)

    return merged
