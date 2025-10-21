# assignment_utils.py
# Load/save/validate per-student assignment mappings for flexible slots (S.C.E., F.E.C., etc.)

from __future__ import annotations
import os
import pandas as pd
from typing import Dict, Tuple, List
from config import get_allowed_assignment_types

# -----------------------------
# Persist & load
# -----------------------------

def load_assignments(db_path: str = "assignments.db", csv_path: str | None = None) -> Dict[str, Dict[str, str]]:
    """
    Reads a simple CSV of assignments into:
        { student_id: { "<AssignmentType>": "<CourseCode>", "_note": "<optional>" }, ... }

    CSV expected columns:
        ID, AssignmentType, Course [, Note]

    db_path is accepted for backward-compatibility but not used here.
    """
    if not csv_path or not os.path.exists(csv_path):
        return {}

    df = pd.read_csv(csv_path)
    # Normalize columns
    for col in ["ID", "AssignmentType", "Course"]:
        if col not in df.columns:
            return {}

    out: Dict[str, Dict[str, str]] = {}
    for _, row in df.iterrows():
        sid = str(row["ID"])
        at  = str(row["AssignmentType"]).strip()
        crs = str(row["Course"]).strip()
        if not sid or not at or not crs:
            continue
        out.setdefault(sid, {})[at] = crs

    if "Note" in df.columns:
        for _, row in df[df["Note"].notna()].iterrows():
            sid = str(row["ID"])
            note = str(row["Note"])
            if sid:
                out.setdefault(sid, {})["_note"] = note

    return out


def save_assignments(assignments: Dict[str, Dict[str, str]], csv_path: str) -> None:
    """
    Writes the mapping back to CSV with columns:
        ID, AssignmentType, Course, Note
    """
    rows: List[dict] = []
    for sid, mapping in assignments.items():
        note = mapping.get("_note", "")
        for atype, crs in mapping.items():
            if atype == "_note":
                continue
            rows.append({"ID": sid, "AssignmentType": atype, "Course": crs, "Note": note})

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)


def reset_assignments(csv_path: str) -> None:
    """Deletes the CSV file if present."""
    if csv_path and os.path.exists(csv_path):
        os.remove(csv_path)

# -----------------------------
# Validation
# -----------------------------

def validate_assignments(
    edited_extra_courses_df: pd.DataFrame,
    existing_assignments: Dict[str, Dict[str, str]]
) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """
    Returns (errors, updated_assignments_mapping).

    Inputs:
      - edited_extra_courses_df: output of ui_components.add_assignment_selection(),
        must have columns ["ID","NAME","Course","AssignTo"] (others tolerated).
      - existing_assignments: current mapping {sid: {atype: course, ...}, ...}

    Rules:
      - AssignTo must be one of the *current* allowed assignment types.
      - For each student, a given AssignTo slot can be used at most once.
    """
    errors: List[str] = []
    updated: Dict[str, Dict[str, str]] = {sid: mapping.copy() for sid, mapping in existing_assignments.items()}

    # Pull dynamic list NOW (reflects Customize Courses override)
    allowed_types = [str(x) for x in get_allowed_assignment_types()]

    # Build a usage map to prevent duplicate use of the same slot per student
    used_by_student: Dict[str, set] = {}
    for sid, mapping in updated.items():
        used_by_student[sid] = {
            k for k in mapping.keys() if k != "_note"
        }

    # Walk the edited rows
    if "AssignTo" not in edited_extra_courses_df.columns:
        return errors, updated

    for _, row in edited_extra_courses_df.iterrows():
        sid = str(row.get("ID", "")).strip()
        course = str(row.get("Course", "")).strip()
        atype = str(row.get("AssignTo", "— None —")).strip()

        if not sid or not course:
            continue

        if atype in ("", "— None —"):
            # No assignment chosen, skip (don’t remove existing mappings here)
            continue

        if atype not in allowed_types:
            errors.append(f"Invalid assignment type '{atype}' for student {sid} / course {course}.")
            continue

        used = used_by_student.setdefault(sid, set())
        if atype in used:
            errors.append(f"Student {sid}: slot '{atype}' already used.")
            continue

        # OK → record
        updated.setdefault(sid, {})[atype] = course
        used.add(atype)

    return errors, updated
