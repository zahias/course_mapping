# 5_Student_Progress.py
import pandas as pd
import streamlit as st
from io import BytesIO
from data_processing import read_progress_report

st.set_page_config(page_title="Student Progress", page_icon="📈", layout="wide")

def _semester_order_key(sem: str) -> int:
    if not isinstance(sem, str):
        return 99
    s = sem.strip().lower()
    # tune this if your institution uses different terms
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

def _get_long_progress_df():
    """
    Try to use a long-form progress DataFrame from session_state.
    If not found, allow the user to upload a progress report here.
    The reader accepts both long-form and wide-form files.
    """
    # Prefer what the app may have already loaded
    for key in ("progress_long_df", "progress_report_long", "long_progress_df"):
        if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
            df = st.session_state[key]
            needed = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
            if needed.issubset(df.columns):
                return df.copy()

    st.info("No long-form progress data found in memory. Upload a progress report below.")

    uploaded = st.file_uploader(
        "Upload Progress Report (.xlsx/.xls/.csv)",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
        key="student_progress_uploader"
    )
    if not uploaded:
        return None

    # read_progress_report now accepts both path-like and UploadedFile
    df = read_progress_report(uploaded)
    if df is None:
        return None

    # Cache for other pages if desired
    st.session_state["progress_long_df"] = df.copy()
    return df

def _export_student_history_to_excel(student_name, student_id, hist_df: pd.DataFrame) -> bytes:
    """
    Export a student's course history to an Excel file in-memory.
    """
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        # Write a small header sheet with metadata
        meta = pd.DataFrame({
            "Field": ["Student Name", "Student ID"],
            "Value": [student_name, student_id]
        })
        meta.to_excel(writer, index=False, sheet_name="Info")

        # Write the detailed history
        # Columns: Year, Semester, Course, Grade
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

    long_df = _get_long_progress_df()
    if long_df is None or long_df.empty:
        st.stop()

    # Clean / normalize basics
    must_cols = ["ID", "NAME", "Course", "Grade", "Year", "Semester"]
    missing = [c for c in must_cols if c not in long_df.columns]
    if missing:
        st.error(f"Uploaded/loaded progress report is missing columns: {missing}")
        st.stop()

    # Normalization
    long_df["Course"] = long_df["Course"].astype(str).str.strip().str.upper()
    long_df["Grade"] = long_df["Grade"].astype(str).str.strip().str.upper()
    long_df["Semester"] = long_df["Semester"].astype(str).str.strip().str.title()
    long_df["Year_int"] = long_df["Year"].apply(_to_int_safe)
    long_df["SemKey"] = long_df["Semester"].apply(_semester_order_key)

    # Student selector
    long_df["ID_str"] = long_df["ID"].astype(str)
    student_options = (
        long_df[["ID_str", "NAME"]]
        .drop_duplicates()
        .assign(label=lambda d: d["ID_str"] + " - " + d["NAME"])
        .sort_values("label")
    )["label"].tolist()

    if not student_options:
        st.warning("No students found in the provided progress report.")
        st.stop()

    selected_label = st.selectbox("Select a student", student_options, index=0)
    sel_id = selected_label.split(" - ")[0]

    student_df = long_df[long_df["ID_str"] == sel_id].copy()
    if student_df.empty:
        st.warning("No records for the selected student.")
        st.stop()

    student_df = student_df.sort_values(["Year_int", "SemKey", "Course"])

    # Header cards
    s_name = student_df["NAME"].iloc[0]
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.metric("Student", s_name)
    c2.metric("ID", sel_id)
    year_span = f"{student_df['Year_int'].min()} – {student_df['Year_int'].max()}" if pd.notna(student_df['Year_int']).any() else "N/A"
    c3.metric("Years Covered", year_span)

    # Group display by Year then Semester
    st.markdown("### Timeline")
    years = student_df["Year_int"].dropna().unique().tolist()
    years = sorted([int(y) for y in years])

    if not years:
        # Fallback if Year was not parseable
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

    # Full flat view (optional)
    with st.expander("Show full table"):
        flat = student_df[["Year_int", "Semester", "Course", "Grade"]].rename(
            columns={"Year_int": "Year"}
        )
        st.dataframe(flat, use_container_width=True, height=400)

    # Download button
    export_df = student_df.rename(columns={"Year_int": "Year"})  # restore Year header
    excel_bytes = _export_student_history_to_excel(s_name, sel_id, export_df)
    st.download_button(
        "Download Course History (Excel)",
        data=excel_bytes,
        file_name=f"{s_name.replace(' ', '_')}_Course_History.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()
