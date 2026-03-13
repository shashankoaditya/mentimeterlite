import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import uuid
import json
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Poll", layout="wide")

# -----------------------------
# FILES
# -----------------------------

QUEST_FILE = "questions.xlsx"
RESP_FILE = "responses.csv"
PART_FILE = "participants.csv"
STATE_FILE = "poll_state.json"

# -----------------------------
# CREATE FILES IF NOT EXIST
# -----------------------------

if not os.path.exists(RESP_FILE):
    pd.DataFrame(columns=["question_id","answer"]).to_csv(RESP_FILE,index=False)

if not os.path.exists(PART_FILE):
    pd.DataFrame(columns=["id"]).to_csv(PART_FILE,index=False)

if not os.path.exists(STATE_FILE):
    with open(STATE_FILE,"w") as f:
        json.dump({"poll_state":"waiting","q_index":0},f)

# -----------------------------
# LOAD QUESTIONS
# -----------------------------

questions_df = pd.read_excel(QUEST_FILE)

# -----------------------------
# STATE FUNCTIONS
# -----------------------------

def get_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE,"w") as f:
        json.dump(state,f)

state = get_state()

# -----------------------------
# URL MODE
# -----------------------------

params = st.query_params
mode = params.get("mode","presenter")

# -----------------------------
# REGISTER PARTICIPANT
# -----------------------------

def register_participant():

    if "participant_id" not in st.session_state:

        pid = str(uuid.uuid4())

        df = pd.read_csv(PART_FILE)

        df.loc[len(df)] = [pid]

        df.to_csv(PART_FILE,index=False)

        st.session_state.participant_id = pid

# -----------------------------
# PRESENTER SCREEN
# -----------------------------

if mode == "presenter":

    st.title("📊 Live Poll Presenter")

    col1,col2 = st.columns([2,1])

    with col1:

        if state["poll_state"] == "waiting":
            st_autorefresh(interval=2000, key="participant_refresh")

            st.subheader("Participants Joining")

            df = pd.read_csv(PART_FILE)

            st.metric("Participants Joined", len(df))

            if st.button("Start Poll"):

                state["poll_state"] = "question"

                save_state(state)

                st.rerun()

        elif state["poll_state"] == "question":

            q = questions_df.iloc[state["q_index"]]

            question_text = q["question"]

            options = [
            q["option1"],
            q["option2"],
            q["option3"],
            q["option4"]
            ]

            st.header(question_text)

            st_autorefresh(interval=2000,key="chartrefresh")

            df = pd.read_csv(RESP_FILE)

            data = df[df["question_id"] == q["question_id"]]

            if len(data)>0:



            # prepare all options with zero votes
                chart_data = pd.Series(0, index=options)

# count votes
                vote_counts = data["answer"].value_counts()

# update counts
                chart_data.update(vote_counts)

                st.bar_chart(chart_data)

            else:

                st.info("Waiting for responses")

            if st.button("Next Question"):

                state["q_index"] += 1

                save_state(state)

                st.rerun()

    with col2:

        st.subheader("Scan to Join")

        poll_url = st.query_params.get("base","") 
        poll_url = st.get_option("server.baseUrlPath")

        join_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

        qr = qrcode.make(join_url)

        buffer = BytesIO()

        qr.save(buffer, format="PNG")

        st.image(buffer.getvalue(), width=250)

        st.caption("Participants scan this QR")

# -----------------------------
# PARTICIPANT SCREEN
# -----------------------------

elif mode == "participant":

    register_participant()

    st_autorefresh(interval=2000,key="participantrefresh")

    state = get_state()

    if state["poll_state"] == "waiting":

        st.title("You are in the waiting zone")

        st.info("We will begin shortly")

    elif state["poll_state"] == "question":

        q = questions_df.iloc[state["q_index"]]

        question_text = q["question"]

        options = [
        q["option1"],
        q["option2"],
        q["option3"],
        q["option4"]
        ]

        st.title(question_text)

        answer = st.radio("Choose your answer",options)

        if st.button("Submit"):

            new = pd.DataFrame({
            "question_id":[q["question_id"]],
            "answer":[answer]
            })

            df = pd.read_csv(RESP_FILE)

            df = pd.concat([df,new],ignore_index=True)

            df.to_csv(RESP_FILE,index=False)

            st.success("Response recorded")
