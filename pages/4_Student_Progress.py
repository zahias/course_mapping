# 5_Student_Progress.py
import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="Student Progress", page_icon="📈", layout="wide")

def _semester_order_key(sem: str) -> int:
    """Order semesters for sorting (adjust if your institution differs)."""
    if not isinstance(sem, str):
        return 99
    s = sem.strip().lower()
    if s in ("winter",):
        return 0
    if s in ("spring",):
        return 1
    if s in ("summer",):
        return 2
    if s in ("fall", "autumn"):
        return 3
    return 99

def _to_int_safe(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None

def _export_student_history_to_excel(student_name, student_id, hist_df: pd.DataFrame) -> bytes:
    """
    Export a student's course history to an Excel file in-memory.
    """
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        # Metadata sheet
        meta = pd.DataFrame({
            "Field": ["Student Name", "Student ID"],
            "Value": [student_name, student_id]
        })
        meta.to_excel(writer, index=False, sheet_name="Info")

        # History sheet
        out_df = hist_df[["Year", "Semester", "Course", "Grade"]].copy()
        out_df.to_excel(writer, index=False, sheet_name="Course History")

        # Autosize columns (best-effort)
        ws_hist = writer.sheets["Course History"]
        for col in ws_hist.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws_hist.column_dimensions[col_letter].width = min(max_len + 2, 50)

        ws_info = writer.sheets["Info"]
        for col in ws_info.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws_info.column_dimensions[col_letter].width = min(max_len + 2, 50)

    bio.seek(0)
    return bio.getvalue()

def main():
    st.title("📈 Student Progress (Across Years)")

    # ---- Source of truth: long-form progress in session ----
    # Populated by the Main page when the progress report is loaded/reloaded.
    df_key_candidates = ("progress_long_df", "progress_report_long", "long_progress_df")
    long_df = None
    for k in df_key_candidates:
        if k in st.session_state and isinstance(st.session_state[k], pd.DataFrame):
            cand = st.session_state[k]
            need = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
            if need.issubset(cand.columns):
                long_df = cand.copy()
                break

    if long_df is None or long_df.empty:
        st.warning(
            "No progress data available yet. "
            "Please load the progress report on the **Main** page."
        )
        # If you’re on Streamlit >= 1.32, you can uncomment the button below for quick navigation:
        # if st.button("Go to Main page"):
        #     st.switch_page("main.py")
        st.stop()

    # ---- Normalization (non-destructive) ----
    must_cols = ["ID", "NAME", "Course", "Grade", "Year", "Semester"]
    missing = [c for c in must_cols if c not in long_df.columns]
    if missing:
        st.error(f"Loaded progress report is missing columns: {missing}")
        st.stop()

    long_df["Course"] = long_df["Course"].astype(str).str.strip().str.upper()
    long_df["Grade"] = long_df["Grade"].astype(str).str.strip().str.upper()
    long_df["Semester"] = long_df["Semester"].astype(str).str.strip().str.title()
    long_df["Year_int"] = long_df["Year"].apply(_to_int_safe)
    long_df["SemKey"] = long_df["Semester"].apply(_semester_order_key)
    long_df["ID_str"] = long_df["ID"].astype(str)

    # ---- Student selector ----
    student_options = (
        long_df[["ID_str", "NAME"]]
        .drop_duplicates()
        .assign(label=lambda d: d["ID_str"] + " - " + d["NAME"])
        .sort_values("label")
    )["label"].tolist()

    if not student_options:
        st.warning("No students found in progress data.")
        st.stop()

    selected_label = st.selectbox("Select a student", student_options, index=0)
    sel_id = selected_label.split(" - ")[0]

    student_df = long_df[long_df["ID_str"] == sel_id].copy()
    if student_df.empty:
        st.warning("No records for the selected student.")
        st.stop()

    student_df = student_df.sort_values(["Year_int", "SemKey", "Course"])

    # ---- Header cards ----
    s_name = student_df["NAME"].iloc[0]
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.metric("Student", s_name)
    c2.metric("ID", sel_id)
    if pd.notna(student_df["Year_int"]).any():
        y_min = int(student_df["Year_int"].dropna().min())
        y_max = int(student_df["Year_int"].dropna().max())
        c3.metric("Years Covered", f"{y_min} – {y_max}")
    else:
        c3.metric("Years Covered", "N/A")

    # ---- Timeline (Year ➜ Semester ➜ Courses/Grades) ----
    st.markdown("### Timeline")
    years = student_df["Year_int"].dropna().unique().tolist()
    years = sorted([int(y) for y in years]) if years else []

    if not years:
        # Fallback if Year wasn’t parseable
        block = student_df[["Year", "Semester", "Course", "Grade"]].rename(
            columns={"Year": "Year (raw)"}
        )
        st.dataframe(block, use_container_width=True, height=500)
    else:
        for y in years:
            year_block = student_df[student_df["Year_int"] == y]
            st.markdown(f"#### {y}")
            sems = (
                year_block[["Semester", "SemKey"]]
                .drop_duplicates()
                .sort_values("SemKey")["Semester"]
                .tolist()
            )
            for sem in sems:
                sem_block = year_block[year_block["Semester"] == sem]
                st.markdown(f"**{sem}**")
                display = sem_block[["Course", "Grade"]].reset_index(drop=True)
                st.dataframe(display, use_container_width=True)

    # ---- Optional: full flat view ----
    with st.expander("Show full table"):
        flat = student_df[["Year_int", "Semester", "Course", "Grade"]].rename(
            columns={"Year_int": "Year"}
        )
        st.dataframe(flat, use_container_width=True, height=400)

    # ---- Download ----
    export_df = student_df.rename(columns={"Year_int": "Year"})
    excel_bytes = _export_student_history_to_excel(s_name, sel_id, export_df)
    st.download_button(
        "Download Course History (Excel)",
        data=excel_bytes,
        file_name=f"{s_name.replace(' ', '_')}_Course_History.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()
