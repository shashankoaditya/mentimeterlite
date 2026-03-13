import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
import uuid
import json
from streamlit_autorefresh import st_autorefresh
import altair as alt

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

            # -----------------------------
            # PREPARE CHART DATA
            # -----------------------------

            chart_data = pd.Series(0, index=options)

            vote_counts = data["answer"].value_counts()

            chart_data.update(vote_counts)

            chart_df = chart_data.reset_index()
            chart_df.columns = ["Option","Votes"]

            # option colors
            color_scale = alt.Scale(
                domain=options,
                range=["#FF4B4B","#4CAF50","#2196F3","#FFC107"]
            )

            chart = alt.Chart(chart_df).mark_bar().encode(
                x=alt.X('Option:N', axis=alt.Axis(labelAngle=0)),
                y='Votes:Q',
                color=alt.Color('Option:N', scale=color_scale, legend=None)
            ).properties(height=400)

            st.altair_chart(chart, use_container_width=True)

            # -----------------------------
            # NAVIGATION BUTTONS
            # -----------------------------

            colA,colB,colC = st.columns(3)

            with colA:

                if st.button("Previous Question"):

                    if state["q_index"] > 0:

                        state["q_index"] -= 1

                        save_state(state)

                        st.rerun()

            with colB:

                if st.button("Next Question"):

                    if state["q_index"] < len(questions_df)-1:

                        state["q_index"] += 1

                        save_state(state)

                        st.rerun()

            with colC:

                if st.button("Restart Quiz"):

                    state["q_index"] = 0
                    state["poll_state"] = "waiting"

                    pd.DataFrame(columns=["question_id","answer"]).to_csv(RESP_FILE,index=False)

                    save_state(state)

                    st.rerun()

    with col2:

        st.subheader("Scan to Join")

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

        option_colors = ["#FF4B4B","#4CAF50","#2196F3","#FFC107"]

        st.title(question_text)

        for i,opt in enumerate(options):

            st.markdown(
                f"""
                <div style="
                padding:10px;
                border-radius:8px;
                background:{option_colors[i]};
                color:white;
                margin-bottom:6px;">
                {opt}
                </div>
                """,
                unsafe_allow_html=True
            )

        answer = st.radio("Choose your answer", options)

        if st.button("Submit"):

            new = pd.DataFrame({
                "question_id":[q["question_id"]],
                "answer":[answer]
            })

            df = pd.read_csv(RESP_FILE)

            df = pd.concat([df,new],ignore_index=True)

            df.to_csv(RESP_FILE,index=False)

            st.success("Response recorded")
