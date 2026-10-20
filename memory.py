import streamlit as st

def get_history():
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    return st.session_state["chat_history"]

def add_message(role, content):
    history = get_history()
    history.append({"role": role, "content": content})
    # Keep only the latest 20 messages in the UI session.
    st.session_state["chat_history"] = history[-20:]

def clear_history():
    st.session_state["chat_history"] = []
