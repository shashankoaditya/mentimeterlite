import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Poll", layout="wide")

RESP_FILE = "responses.csv"

questions = [
{
"id":1,
"question":"What does AI stand for?",
"options":[
"Artificial Intelligence",
"Automated Internet",
"Advanced Interface",
"Algorithmic Input"
]
}
]

# create response file
if not os.path.exists(RESP_FILE):
    pd.DataFrame(columns=["question_id","answer"]).to_csv(RESP_FILE,index=False)

# session state
if "poll_state" not in st.session_state:
    st.session_state.poll_state = "waiting"

params = st.query_params
mode = params.get("mode","home")

# -----------------------------
# LANDING PAGE (SHOW QR)
# -----------------------------

if mode == "home":

    st.title("📊 Live Poll")

    st.subheader("Scan the QR code to join")

    poll_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

    qr = qrcode.make(poll_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    st.image(buffer.getvalue(), width=300)

    st.write("Use your phone camera to scan and join")

# -----------------------------
# PRESENTER DASHBOARD
# -----------------------------

elif mode == "presenter":

    st.title("Presenter Dashboard")

    if st.session_state.poll_state == "waiting":

        st.header("Audience Joining")

        if st.button("Start Question"):

            st.session_state.poll_state = "question"

    elif st.session_state.poll_state == "question":

        q = questions[0]

        st.header(q["question"])

        st_autorefresh(interval=2000, key="refresh")

        df = pd.read_csv(RESP_FILE)

        data = df[df["question_id"]==q["id"]]

        if len(data)>0:

            chart = data["answer"].value_counts()

            st.bar_chart(chart)

        else:

            st.info("Waiting for responses")

# -----------------------------
# PARTICIPANT PAGE
# -----------------------------

elif mode == "participant":

    if st.session_state.poll_state == "waiting":

        st.title("Connected")

        st.info("Please wait for the first question")

    elif st.session_state.poll_state == "question":

        q = questions[0]

        st.title(q["question"])

        answer = st.radio(
        "Choose your answer",
        q["options"]
        )

        if st.button("Submit"):

            new = pd.DataFrame({
            "question_id":[q["id"]],
            "answer":[answer]
            })

            df = pd.read_csv(RESP_FILE)

            df = pd.concat([df,new],ignore_index=True)

            df.to_csv(RESP_FILE,index=False)

            st.success("Vote submitted")
