import streamlit as st

# Import each page as a function
from pages.upload_data import upload_data_page
from pages.customize_courses import customize_courses_page
from pages.view_reports import view_reports_page
from pages.student_profiles import student_profiles_page

PAGES = {
    "📤 Upload Data": upload_data_page,
    "⚙️ Customize Courses": customize_courses_page,
    "📊 View Reports": view_reports_page,
    "👤 Student Profiles": student_profiles_page
}

st.set_page_config(
    page_title="Phoenicia University Student Progress Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# — Global stylesheet —
st.markdown(
    """
    <style>
      /* Sidebar */
      .css-1d391kg {background-color: #f0f2f6;}
      /* Buttons */
      .stButton>button {background-color: #003366; color: white;}
      .stButton>button:hover {background-color: #005599;}
      /* Footer bar */
      footer {visibility: hidden;}
      /* Table header */
      .css-1q8dd3e th {background-color: #003366 !important; color: white !important;}
    </style>
    """,
    unsafe_allow_html=True
)

# — Sidebar navigation —
with st.sidebar:
    st.title("Navigation")
    choice = st.radio("Go to", list(PAGES.keys()), index=list(PAGES.keys()).index("📤 Upload Data"))

# — Render the selected page —
page_fn = PAGES[choice]
page_fn()

# — Persistent footer bar —
st.markdown(
    """
    <hr style="margin:2rem 0; border:1px solid #ddd;">
    <div style="
      position:fixed; bottom:0; left:0; width:100%;
      background:#f5f5f5; padding:0.5rem; text-align:center;
      font-size:0.9rem; color:#444;">
      Developed by Dr. Zahi Abdul Sater
    </div>
    """,
    unsafe_allow_html=True
)
