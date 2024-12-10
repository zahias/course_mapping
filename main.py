import streamlit as st

st.set_page_config(page_title="Phoenicia University Student Progress Tracker", layout="wide")

st.image("pu_logo.png", width=120)
st.title("Phoenicia University Student Progress Tracker")
st.subheader("Developed by Dr. Zahi Abdul Sater")

st.markdown("Welcome to the Phoenicia University Student Progress Tracker.")
st.markdown("---")

st.markdown("**Instructions:**")
st.markdown("- Go to **Upload Data** to load your progress report and equivalent courses.")
st.markdown("- Go to **Customize Courses** to define required and intensive courses.")
st.markdown("- Go to **View Reports** to see and filter processed data.")
st.markdown("- Go to **Student Profiles** to explore individual academic journeys by year and semester.")

st.markdown("Use the sidebar or the multipage navigation to move between sections.")
