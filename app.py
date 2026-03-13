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

QUEST_FILE = "questions.xlsx"
RESP_FILE = "responses.csv"
PART_FILE = "participants.csv"
STATE_FILE = "poll_state.json"

if not os.path.exists(RESP_FILE):
pd.DataFrame(columns=["question_id","participant_id","answer"]).to_csv(RESP_FILE,index=False)

if not os.path.exists(PART_FILE):
pd.DataFrame(columns=["id"]).to_csv(PART_FILE,index=False)

if not os.path.exists(STATE_FILE):
with open(STATE_FILE,"w") as f:
json.dump({"poll_state":"waiting","q_index":0},f)

questions_df = pd.read_excel(QUEST_FILE)

def get_state():
with open(STATE_FILE) as f:
return json.load(f)

def save_state(state):
with open(STATE_FILE,"w") as f:
json.dump(state,f)

state = get_state()

params = st.query_params
mode = params.get("mode","presenter")

def register_participant():
if "participant_id" not in st.session_state:
pid = str(uuid.uuid4())
df = pd.read_csv(PART_FILE)
df.loc[len(df)] = [pid]
df.to_csv(PART_FILE,index=False)
st.session_state.participant_id = pid

# -------------------------

# PRESENTER

# -------------------------

if mode == "presenter":

```
st.title("📊 Live Poll Presenter")

col1, col2 = st.columns([3,1])

with col1:

    if state["poll_state"] == "waiting":

        st_autorefresh(interval=2000)

        st.subheader("Participants Joining")

        df = pd.read_csv(PART_FILE)

        st.metric("Participants Joined", len(df))

        if st.button("Start Poll"):
            state["poll_state"] = "question"
            save_state(state)
            st.rerun()


    elif state["poll_state"] == "question":

        q = questions_df.iloc[state["q_index"]]

        options = [
            q["option1"],
            q["option2"],
            q["option3"],
            q["option4"]
        ]

        st.header(q["question"])

        st_autorefresh(interval=2000)

        df = pd.read_csv(RESP_FILE)

        data = df[df["question_id"] == q["question_id"]]

        chart_data = pd.Series(0, index=options)

        vote_counts = data["answer"].value_counts()

        chart_data.update(vote_counts)

        chart_df = chart_data.reset_index()

        chart_df.columns = ["Option","Votes"]

        chart_df["Color"] = [
            "#FFC107",
            "#FF4B4B",
            "#4CAF50",
            "#2196F3"
        ]

        chart = alt.Chart(chart_df).mark_bar(size=80).encode(
            x=alt.X("Option:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Votes:Q", axis=alt.Axis(title="Votes")),
            color=alt.Color("Color:N", scale=None)
        ).properties(height=420)

        st.altair_chart(chart, use_container_width=True)

        colA, colB, colC = st.columns(3)

        with colA:
            if st.button("⬅ Previous Question"):
                if state["q_index"] > 0:
                    state["q_index"] -= 1
                    save_state(state)
                    st.rerun()

        with colB:
            if st.button("Next Question ➡"):
                if state["q_index"] < len(questions_df)-1:
                    state["q_index"] += 1
                    save_state(state)
                    st.rerun()

        with colC:
            if st.button("🔄 Restart Quiz"):
                state["q_index"] = 0
                state["poll_state"] = "waiting"

                pd.DataFrame(
                    columns=["question_id","participant_id","answer"]
                ).to_csv(RESP_FILE,index=False)

                pd.DataFrame(columns=["id"]).to_csv(PART_FILE,index=False)

                save_state(state)

                st.rerun()

with col2:

    st.subheader("Scan to Join")

    join_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

    qr = qrcode.make(join_url)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    st.image(buffer.getvalue(), width=260)

    st.caption("Participants scan this QR")
```

# -------------------------

# PARTICIPANT

# -------------------------

if mode == "participant":

```
register_participant()

st_autorefresh(interval=2000)

state = get_state()

if state["poll_state"] == "waiting":

    st.title("You are in the waiting zone")

    st.info("We will begin shortly")


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

    if st.button("Submit"):

        pid = st.session_state.participant_id

        df = pd.read_csv(RESP_FILE)

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
