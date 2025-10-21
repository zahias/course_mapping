import streamlit as st
import pandas as pd
import os
import json
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    update_file,
    upload_file,
    download_file
)
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define courses configuration for the selected Major. The CSV must contain:\n\n"
    "- **Course** (e.g. PBHL201)\n"
    "- **Credits** (integer)\n"
    "- **PassingGrades** (comma-separated list, e.g. A+,A,A-,B)\n"
    "- **Type** (`Required` or `Intensive`)\n"
    "- **FromSemester** (e.g. FALL-2016) or leave blank for no lower bound\n"
    "- **ToSemester**   (e.g. SUMMER-9999) or leave blank for no upper bound\n\n"
    "Semesters must follow `FALL-YYYY`, `SPRING-YYYY`, or `SUMMER-YYYY` exactly."
)

# === 0) Major Selection ===
if "selected_major" not in st.session_state or st.session_state["selected_major"] is None:
    st.warning("First, select a Major on the Upload Data page.")
    st.stop()

major = st.session_state["selected_major"]

# Ensure local folder exists
local_folder = os.path.join("configs", major)
os.makedirs(local_folder, exist_ok=True)

# Small helpers for Drive paths
def _drive_path(filename: str) -> str:
    return f"configs/{major}/{filename}"

def _local_path(filename: str) -> str:
    return os.path.join(local_folder, filename)

# ===== Assignment Types: load from Drive (or local) on page load so they persist across refreshes =====
ASSIGN_TYPES_FILENAME = "assignment_types.json"
assign_types_local = _local_path(ASSIGN_TYPES_FILENAME)
assign_types_drive = _drive_path(ASSIGN_TYPES_FILENAME)

def _load_assignment_types():
    # Try Drive first → local file → default
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        fid = search_file(service, assign_types_drive)
        if fid:
            download_file(service, fid, assign_types_local)
    except Exception:
        # Silently ignore if drive is not configured
        pass

    if os.path.exists(assign_types_local):
        try:
            with open(assign_types_local, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return [str(x) for x in data if str(x).strip()]
        except Exception:
            pass
    # Default if nothing found
    return ["S.C.E", "F.E.C"]

# Initialize session_state for this major from persisted file (if not already set)
key_per_major_types = f"{major}_allowed_assignment_types"
if key_per_major_types not in st.session_state:
    st.session_state[key_per_major_types] = _load_assignment_types()

# === 1) Course Configuration Section ===
with st.expander("Course Configuration Options", expanded=True):
    uploaded_courses = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="Use the template below."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template"):
            template_df = pd.DataFrame([
                {
                    "Course":        "PBHL201",
                    "Credits":       3,
                    "PassingGrades": "C-,C,C+",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2016",
                    "ToSemester":    "SPRING-2018"
                },
                {
                    "Course":        "PBHL201",
                    "Credits":       3,
                    "PassingGrades": "C+,C",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2018",
                    "ToSemester":    "SUMMER-9999"
                },
                {
                    "Course":        "MATH102",
                    "Credits":       3,
                    "PassingGrades": "D-,D",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2015",
                    "ToSemester":    "SUMMER-2019"
                },
                {
                    "Course":        "MATH102",
                    "Credits":       3,
                    "PassingGrades": "C-,C",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2019",
                    "ToSemester":    "SUMMER-9999"
                },
                {
                    "Course":        "INEG200",
                    "Credits":       3,
                    "PassingGrades": "A+,A,A-",
                    "Type":          "Intensive",
                    "FromSemester":  "FALL-2015",
                    "ToSemester":    "SUMMER-9999"
                },
            ])
            st.download_button(
                "Download Courses Template",
                data=template_df.to_csv(index=False).encode("utf-8"),
                file_name="courses_template.csv",
                mime="text/csv"
            )
    with col2:
        if st.button("Reload Courses Configuration from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                drive_name = _drive_path("courses_config.csv")
                file_id = search_file(service, drive_name)
                if file_id:
                    local_csv = _local_path("courses_config.csv")
                    download_file(service, file_id, local_csv)
                    st.success("Reloaded courses_config.csv from Google Drive.")
                else:
                    st.error("No courses_config.csv found on Google Drive for this Major.")
            except Exception as e:
                st.error(f"Error reloading courses configuration: {e}")

    # --- Load or Sync the CSV ---
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
            local_csv = _local_path("courses_config.csv")
            courses_df.to_csv(local_csv, index=False)

            # Sync to Drive
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                drive_name = _drive_path("courses_config.csv")
                file_id = search_file(service, drive_name)
                if file_id:
                    update_file(service, file_id, local_csv)
                else:
                    upload_file(service, local_csv, drive_name)
                st.success("Courses configuration synced to Google Drive.")
            except Exception as e:
                st.warning(f"Could not sync to Google Drive: {e}")
        except Exception as e:
            st.error(f"Error reading uploaded courses CSV: {e}")
    elif os.path.exists(_local_path("courses_config.csv")):
        courses_df = pd.read_csv(_local_path("courses_config.csv"))
    else:
        courses_df = None

    # --- Parse into in‐memory rule tables and credit maps ---
    if courses_df is not None:
        required_cols = {
            "Course", "Credits", "PassingGrades",
            "Type", "FromSemester", "ToSemester"
        }
        if required_cols.issubset(courses_df.columns):
            def sem_to_ord(s: str, lower: bool):
                if pd.isna(s) or str(s).strip() == "":
                    return float('-inf') if lower else float('inf')
                sem, yr = str(s).split("-")
                return int(yr) * 3 + {"FALL": 0, "SPRING": 1, "SUMMER": 2}[sem.upper()]

            target_rules = {}
            intensive_rules = {}
            required_credits = {}
            intensive_credits = {}

            for _, row in courses_df.iterrows():
                course   = str(row["Course"]).strip().upper()
                creds    = int(row["Credits"])
                pg       = str(row["PassingGrades"]).strip()
                typ      = str(row["Type"]).strip().lower()
                fr_ord   = sem_to_ord(row["FromSemester"], lower=True)
                to_ord   = sem_to_ord(row["ToSemester"],   lower=False)
                rule_dict = {
                    "Credits":       creds,
                    "PassingGrades": pg,
                    "FromOrd":       fr_ord,
                    "ToOrd":         to_ord
                }

                if typ == "required":
                    required_credits[course] = creds
                    target_rules.setdefault(course, []).append(rule_dict)
                else:
                    intensive_credits[course] = creds
                    intensive_rules.setdefault(course, []).append(rule_dict)

            # Save into session_state under Major‐scoped keys
            st.session_state[f"{major}_target_course_rules"]    = target_rules
            st.session_state[f"{major}_intensive_course_rules"] = intensive_rules
            st.session_state[f"{major}_target_courses"]         = required_credits
            st.session_state[f"{major}_intensive_courses"]      = intensive_credits

            st.success("Courses configuration loaded successfully.")
        else:
            st.error(
                "CSV must contain columns: " + ", ".join(sorted(required_cols))
            )
    else:
        st.info("No courses configuration available. Please upload a file.")

# === 2) Equivalent Courses Section — NOW EDITABLE ===
with st.expander("Equivalent Courses", expanded=False):
    st.write("Edit the `equivalent_courses.csv` for this Major. Format:")
    st.code("Course, Equivalent\nPBHL201, PBHL201A\nMATH102, MATH202", language="text")

    # Ensure file exists locally (download or create)
    local_eq = _local_path("equivalent_courses.csv")
    try:
        creds = authenticate_google_drive()
        service = build("drive", "v3", credentials=creds)
        fid = search_file(service, _drive_path("equivalent_courses.csv"))
        if fid:
            download_file(service, fid, local_eq)
    except Exception:
        pass

    if os.path.exists(local_eq):
        eq_df = pd.read_csv(local_eq)
    else:
        eq_df = pd.DataFrame(columns=["Course", "Equivalent"])
        # Create an empty file both locally and on Drive
        eq_df.to_csv(local_eq, index=False)
        try:
            upload_file(service, local_eq, _drive_path("equivalent_courses.csv"))
        except Exception:
            pass

    # Clean columns and show editor
    if "Course" not in eq_df.columns or "Equivalent" not in eq_df.columns:
        missing = {"Course", "Equivalent"} - set(eq_df.columns)
        st.error(f"Missing columns in equivalent_courses.csv: {missing}")
    else:
        edited_eq_df = st.data_editor(
            eq_df[["Course", "Equivalent"]],
            num_rows="dynamic",
            use_container_width=True,
            key=f"eq_editor_{major}"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save Equivalent Courses"):
                try:
                    # Drop fully empty rows
                    cleaned = edited_eq_df.copy()
                    cleaned["Course"] = cleaned["Course"].astype(str).str.strip().str.upper()
                    cleaned["Equivalent"] = cleaned["Equivalent"].astype(str).str.strip().str.upper()
                    cleaned = cleaned[(cleaned["Course"] != "") & (cleaned["Equivalent"] != "")]
                    cleaned.to_csv(local_eq, index=False)

                    # Push to Drive
                    try:
                        fid = search_file(service, _drive_path("equivalent_courses.csv"))
                        if fid:
                            update_file(service, fid, local_eq)
                        else:
                            upload_file(service, local_eq, _drive_path("equivalent_courses.csv"))
                        st.success("Equivalent courses saved to Google Drive.")
                    except Exception as e:
                        st.warning(f"Saved locally but could not sync to Drive: {e}")
                except Exception as e:
                    st.error(f"Error saving equivalent courses: {e}")
        with c2:
            if st.button("Reload from Google Drive"):
                try:
                    fid = search_file(service, _drive_path("equivalent_courses.csv"))
                    if fid:
                        download_file(service, fid, local_eq)
                        st.success("Reloaded equivalent courses from Google Drive.")
                        st.rerun()
                    else:
                        st.info("No equivalent_courses.csv on Drive yet.")
                except Exception as e:
                    st.error(f"Error reloading from Drive: {e}")

# === 3) Assignment Types Configuration — PERSISTED TO DRIVE ===
with st.expander("Assignment Types Configuration", expanded=False):
    st.write("Edit the list of assignment types (e.g. S.C.E., F.E.C., ARAB201). This is **per Major** and now persisted to Google Drive.")
    current_types = st.session_state.get(key_per_major_types, ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input(
        "Enter assignment types (comma separated)",
        value=", ".join(current_types)
    )

    colA, colB = st.columns(2)
    with colA:
        if st.button("Save Assignment Types"):
            try:
                new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
                # Update session state immediately
                st.session_state[key_per_major_types] = new_types

                # Persist locally
                with open(assign_types_local, "w", encoding="utf-8") as f:
                    json.dump(new_types, f, ensure_ascii=False, indent=2)

                # Sync to Drive
                try:
                    creds = authenticate_google_drive()
                    service = build("drive", "v3", credentials=creds)
                    fid = search_file(service, assign_types_drive)
                    if fid:
                        update_file(service, fid, assign_types_local)
                    else:
                        upload_file(service, assign_types_local, assign_types_drive)
                    st.success("Assignment types saved to Google Drive.")
                except Exception as e:
                    st.warning(f"Saved locally but could not sync to Drive: {e}")
            except Exception as e:
                st.error(f"Error saving assignment types: {e}")

    with colB:
        if st.button("Reload Assignment Types from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                fid = search_file(service, assign_types_drive)
                if fid:
                    download_file(service, fid, assign_types_local)
                    with open(assign_types_local, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, list) and loaded:
                        st.session_state[key_per_major_types] = [str(x) for x in loaded if str(x).strip()]
                        st.success("Assignment types reloaded from Google Drive.")
                        st.rerun()
                    else:
                        st.info("Assignment types file exists but is empty. Using defaults.")
                else:
                    st.info("No assignment_types.json found on Drive for this Major.")
            except Exception as e:
                st.error(f"Error reloading assignment types: {e}")
