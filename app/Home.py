"""Landing page: sidebar habitat picker, disclaimer footer (CLAUDE.md section 9).

Task P1. Run with: streamlit run app/Home.py
app/ imports from core/ and reads files from data/. Never calls the PSI endpoint.
"""
import streamlit as st

st.set_page_config(page_title="Cool Flames — Fire Scenario Explorer", page_icon="🔥")

st.title("Cool Flames — Fire Scenario Explorer")
st.write("Research and reference tool for NASA PSI microgravity combustion data.")

# TODO (P1): sidebar habitat picker (iss, moon_brief, exploration, suit).

st.caption(
    "Research and reference tool, not an operational safety system. "
    "Data: NASA PSI (CC0)."
)
