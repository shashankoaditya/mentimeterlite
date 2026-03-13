import streamlit as st
import pandas as pd
import os
import qrcode
from PIL import Image
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
},

{
"id":2,
"question":"Which company created ChatGPT?",
"options":[
"Google",
"Microsoft",
"OpenAI",
"Amazon"
]
},

{
"id":3,
"question":"Which language is most used for AI?",
"options":[
"Python",
"Java",
"C++",
"ABAP"
]
}
]

if not os.path.exists(RESP_FILE):
    df = pd.DataFrame(columns=["question_id","answer"])
    df.to_csv(RESP_FILE,index=False)

if "q_index" not in st.session_state:
    st.session_state.q_index = 0

st.sidebar.title("Mode")

mode = st.sidebar.radio(
"Select",
["Presenter","Participant"]
)

st.title("📊 Live Team Poll")

# -----------------------------
# PRESENTER
# -----------------------------

if mode == "Presenter":

    col1,col2 = st.columns([2,1])

    with col1:

        q = questions[st.session_state.q_index]

        st.header("Current Question")

        st.subheader(q["question"])

        st.write("Options")

        for op in q["options"]:
            st.write("•",op)

        if st.button("Next Question"):

            if st.session_state.q_index < len(questions)-1:
                st.session_state.q_index +=1

        if st.button("Reset Poll"):

            pd.DataFrame(columns=["question_id","answer"]).to_csv(RESP_FILE,index=False)

    with col2:

        st.header("Join Poll")

        url = st.text_input(
        "App URL",
        "https://your-app.streamlit.app"
        )

        qr = qrcode.make(url)

        st.image(qr,width=200)

        st.write("Scan to join")

    st.header("Live Results")

    st_autorefresh(interval=2000,key="resultsrefresh")

    df = pd.read_csv(RESP_FILE)

    qid = questions[st.session_state.q_index]["id"]

    data = df[df["question_id"]==qid]

    if len(data)>0:

        result = data["answer"].value_counts()

        st.bar_chart(result)

    else:

        st.info("Waiting for responses")

# -----------------------------
# PARTICIPANT
# -----------------------------

if mode == "Participant":

    q = questions[st.session_state.q_index]

    st.header("Vote")

    st.subheader(q["question"])

    answer = st.radio(
    "Choose",
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
