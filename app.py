import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os

st.set_page_config(page_title="Live Poll", layout="wide")

RESP_FILE = "responses.csv"

# questions
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

# session states
if "mode" not in st.session_state:
    st.session_state.mode = "waiting"

if "q_index" not in st.session_state:
    st.session_state.q_index = 0

params = st.query_params
user_mode = params.get("mode","home")

# --------------------------
# PRESENTER
# --------------------------

if user_mode == "presenter":

    st.title("Presenter Dashboard")

    if st.session_state.mode == "waiting":

        st.header("Audience Joining")

        poll_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

        qr = qrcode.make(poll_url)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        st.image(buffer.getvalue(), width=250)

        if st.button("Start First Question"):

            st.session_state.mode = "question"

    elif st.session_state.mode == "question":

        q = questions[st.session_state.q_index]

        st.header(q["question"])

        df = pd.read_csv(RESP_FILE)

        data = df[df["question_id"]==q["id"]]

        if len(data)>0:

            chart = data["answer"].value_counts()

            st.bar_chart(chart)

        else:

            st.info("Waiting for responses")

# --------------------------
# PARTICIPANT
# --------------------------

elif user_mode == "participant":

    if st.session_state.mode == "waiting":

        st.title("Connected")

        st.info("Please wait for the first question")

    elif st.session_state.mode == "question":

        q = questions[st.session_state.q_index]

        st.title(q["question"])

        answer = st.radio(
        "Choose one",
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

            st.success("Response recorded")
