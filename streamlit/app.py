from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from login import show_login
from chat import show_chat

st.markdown("""
<style>
[data-testid="stSidebar"] button[kind="secondary"] {
    background: none;
    border: none;
    box-shadow: none;
    text-align: left;
    padding: 4px 8px;
    margin: 0;
    color: inherit;
    border-radius: 6px;
    transition: background-color 0.15s ease;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: rgba(0, 0, 0, 0.08);
}
[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
    gap: 0;
}
[data-testid="stSidebar"] div.stButton {
    margin-bottom: -12px;
}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    show_login()
else:
    show_chat()
