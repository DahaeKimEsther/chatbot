import uuid
import streamlit as st
from db import get_user, create_user, verify_password, load_messages

def show_login():
    st.title("로그인")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        username = st.text_input("아이디", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인"):
            user = get_user(username)
            if user and verify_password(password, user[2]):
                st.session_state.user = {"id": user[0], "username": user[1]}
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.messages = load_messages(st.session_state.thread_id)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")

    with tab2:
        new_username = st.text_input("아이디", key="register_username")
        new_password = st.text_input("비밀번호", type="password", key="register_password")
        if st.button("회원가입"):
            if get_user(new_username):
                st.error("이미 존재하는 아이디입니다.")
            else:
                create_user(new_username, new_password)
                st.success("회원가입 완료! 로그인해주세요.")
