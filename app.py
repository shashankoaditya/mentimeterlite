import streamlit as st

st.set_page_config(
    page_title="Team Poll",
    layout="wide"
)

st.title("📊 Live Team Poll")

st.sidebar.title("Menu")

mode = st.sidebar.radio(
    "Select Mode",
    ["Presenter", "Participant"]
)

# -------------------------
# PRESENTER SCREEN
# -------------------------

if mode == "Presenter":

    st.header("Presenter Dashboard")

    col1, col2 = st.columns([2,1])

    with col1:
        question = st.text_input("Enter Question")

        st.selectbox(
            "Question Type",
            ["Open Text", "Multiple Choice", "Word Cloud"]
        )

        st.button("Publish Question")

    with col2:
        st.subheader("Session Info")

        st.info("Share this link with participants")

        st.code("app-link-here")

# -------------------------
# PARTICIPANT SCREEN
# -------------------------

if mode == "Participant":

    st.header("Submit Your Answer")

    name = st.text_input("Your Name")

    st.subheader("Current Question")

    st.info("Question will appear here")

    st.text_area("Your Answer")

    st.button("Submit")
