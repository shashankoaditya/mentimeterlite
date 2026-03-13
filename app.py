# ============================================================

# IMPORT LIBRARIES

# ============================================================

# Streamlit → creates the web application UI

import streamlit as st

# Pandas → used to read/write Excel and CSV files

import pandas as pd

# qrcode → used to generate the QR code for participants

import qrcode

# BytesIO → allows images (QR code) to be stored in memory

from io import BytesIO

# os → checks if files exist

import os

# uuid → generates a unique ID for each participant

import uuid

# json → stores poll state (which question is active)

import json

# streamlit_autorefresh → refreshes page automatically for live polling

from streamlit_autorefresh import st_autorefresh

# Altair → chart library used to display poll results

import altair as alt

# ============================================================

# STREAMLIT PAGE SETTINGS

# ============================================================

# Sets page title and layout

st.set_page_config(page_title="Live Poll", layout="wide")

# ============================================================

# BASIC UI STYLING (OPTIONAL)

# ============================================================

# This block styles the buttons so they look nicer

st.markdown("""

<style>

.stButton>button {
    font-size:18px;
    height:55px;
    border-radius:10px;
    border:2px solid #4CAF50;
}

.stButton>button:hover {
    background-color:#4CAF50;
    color:white;
}

</style>

""", unsafe_allow_html=True)

# ============================================================

# FILE NAMES USED BY THE APPLICATION

# ============================================================

# Excel file where your questions are stored

QUEST_FILE = "questions.xlsx"

# CSV file where all responses are stored

RESP_FILE = "responses.csv"

# CSV file where all participants are tracked

PART_FILE = "participants.csv"

# JSON file storing the poll state

STATE_FILE = "poll_state.json"

# ============================================================

# CREATE DATA FILES IF THEY DO NOT EXIST

# ============================================================

# Create response file (stores answers)

if not os.path.exists(RESP_FILE):

    
    pd.DataFrame(
    columns=["question_id","participant_id","answer"]
    ).to_csv(RESP_FILE,index=False)
    

# Create participant file (stores joined users)

if not os.path.exists(PART_FILE):


    pd.DataFrame(columns=["id"]).to_csv(PART_FILE,index=False)


# Create poll state file

if not os.path.exists(STATE_FILE):


    with open(STATE_FILE,"w") as f:

        json.dump(
        {"poll_state":"waiting","q_index":0},
        f
        )


# ============================================================

# LOAD QUESTIONS FROM EXCEL

# ============================================================

# Reads questions.xlsx into a dataframe

questions_df = pd.read_excel(QUEST_FILE)

# ============================================================

# STATE MANAGEMENT FUNCTIONS

# ============================================================

# Read current poll state

def get_state():


    with open(STATE_FILE) as f:

        return json.load(f)


# Save poll state

def save_state(state):


with open(STATE_FILE,"w") as f:

    json.dump(state,f)


# Load current state into memory

state = get_state()

# ============================================================

# DETERMINE USER MODE (PRESENTER OR PARTICIPANT)

# ============================================================

# URL example:

# ?mode=presenter

# ?mode=participant

params = st.query_params

mode = params.get("mode","presenter")

# ============================================================

# REGISTER PARTICIPANT

# ============================================================

# When someone joins via QR code,

# they receive a unique participant ID

def register_participant():


if "participant_id" not in st.session_state:

    pid = str(uuid.uuid4())

    df = pd.read_csv(PART_FILE)

    df.loc[len(df)] = [pid]

    df.to_csv(PART_FILE,index=False)

    st.session_state.participant_id = pid


# ============================================================

# PRESENTER SCREEN

# ============================================================

if mode == "presenter":


    st.title("📊 Live Poll Presenter")

# Split screen into chart area + QR code area
    col1,col2 = st.columns([3,1])


# --------------------------------------------------------
# LEFT SIDE (MAIN CONTROL PANEL)
# --------------------------------------------------------

with col1:

    # Waiting screen
    if state["poll_state"] == "waiting":

        # Auto refresh every 2 seconds
        st_autorefresh(interval=2000)

        st.subheader("Participants Joining")

        df = pd.read_csv(PART_FILE)

        st.metric("Participants Joined", len(df))

        # Start poll button
        if st.button("Start Poll"):

            state["poll_state"] = "question"

            save_state(state)

            st.rerun()


    # --------------------------------------------------------
    # QUESTION SCREEN
    # --------------------------------------------------------

    elif state["poll_state"] == "question":

        # Get current question
        q = questions_df.iloc[state["q_index"]]

        options = [
            q["option1"],
            q["option2"],
            q["option3"],
            q["option4"]
        ]

        st.header(q["question"])

        # Refresh chart every 2 seconds
        st_autorefresh(interval=2000)

        # Load responses
        df = pd.read_csv(RESP_FILE)

        data = df[df["question_id"] == q["question_id"]]

        # Create default vote count
        chart_data = pd.Series(0, index=options)

        vote_counts = data["answer"].value_counts()

        chart_data.update(vote_counts)

        # Convert to dataframe for Altair
        chart_df = chart_data.reset_index()

        chart_df.columns = ["Option","Votes"]

        # Assign colors to options
        chart_df["Color"] = [
            "#FFC107",
            "#FF4B4B",
            "#4CAF50",
            "#2196F3"
        ]

        # Build bar chart
        chart = alt.Chart(chart_df).mark_bar(size=80).encode(

            x=alt.X(
                "Option:N",
                axis=alt.Axis(labelAngle=0)
            ),

            y=alt.Y(
                "Votes:Q",
                axis=alt.Axis(title="Votes")
            ),

            color=alt.Color("Color:N", scale=None)

        ).properties(height=420)

        st.altair_chart(chart, use_container_width=True)


        # --------------------------------------------------------
        # NAVIGATION BUTTONS
        # --------------------------------------------------------

        colA,colB,colC = st.columns(3)


        # Previous question
        with colA:

            if st.button("⬅ Previous Question"):

                if state["q_index"] > 0:

                    state["q_index"] -= 1

                    save_state(state)

                    st.rerun()


        # Next question
        with colB:

            if st.button("Next Question ➡"):

                if state["q_index"] < len(questions_df)-1:

                    state["q_index"] += 1

                    save_state(state)

                    st.rerun()


        # Restart quiz
        with colC:

            if st.button("🔄 Restart Quiz"):

                state["q_index"] = 0
                state["poll_state"] = "waiting"

                # Clear responses
                pd.DataFrame(
                    columns=["question_id","participant_id","answer"]
                ).to_csv(RESP_FILE,index=False)

                # Clear participants
                pd.DataFrame(columns=["id"]).to_csv(PART_FILE,index=False)

                save_state(state)

                st.rerun()


# --------------------------------------------------------
# RIGHT SIDE (QR CODE)
# --------------------------------------------------------

with col2:

    st.subheader("Scan to Join")

    join_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

    qr = qrcode.make(join_url)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    st.image(buffer.getvalue(), width=260)

    st.caption("Participants scan this QR")
```

# ============================================================

# PARTICIPANT SCREEN

# ============================================================

elif mode == "participant":

```
register_participant()

st_autorefresh(interval=2000)

state = get_state()


# Waiting screen
if state["poll_state"] == "waiting":

    st.title("You are in the waiting zone")

    st.info("We will begin shortly")


# Question screen
elif state["poll_state"] == "question":

    q = questions_df.iloc[state["q_index"]]

    options = [
        q["option1"],
        q["option2"],
        q["option3"],
        q["option4"]
    ]

    st.title(q["question"])

    answer = st.radio("Choose your answer", options)


    # Submit answer
    if st.button("Submit"):

        pid = st.session_state.participant_id

        df = pd.read_csv(RESP_FILE)

        # Check if participant already answered
        existing = df[
            (df["question_id"] == q["question_id"]) &
            (df["participant_id"] == pid)
        ]

        if len(existing) > 0:

            st.warning("You already answered this question")

        else:

            new = pd.DataFrame({
                "question_id":[q["question_id"]],
                "participant_id":[pid],
                "answer":[answer]
            })

            df = pd.concat([df,new],ignore_index=True)

            df.to_csv(RESP_FILE,index=False)

            st.success("Response recorded")
```
