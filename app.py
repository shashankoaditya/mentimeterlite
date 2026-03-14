import streamlit as st
import pandas as pd
import json
import uuid
import altair as alt
import qrcode
from streamlit_autorefresh import st_autorefresh

QUESTIONS_FILE = "questions.json"
RESPONSES_FILE = "responses.csv"
PARTICIPANTS_FILE = "participants.csv"
STATE_FILE = "poll_state.json"

# This function reads the questions file and returns it as a pandas DataFrame.
# The app will call this function whenever it needs to display questions.
def load_questions():
    with open("questions.json") as f:
         return json.load(f)

# Load current poll state from poll_state.json
# If the file does not exist (first run), create a default state
# This state controls whether the poll has started and which question is active
def load_state():

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

    except:

        state = {
            "poll_started": False,
            "current_question": 0
        }

        save_state(state)

    return state
# Save the current poll state into poll_state.json
# Called whenever presenter starts poll, moves to next question, or restarts quiz
# Ensures all users see the same poll status

def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# Register a participant when they open the poll
# Generates a unique participant ID and stores it in the session
# Also saves the participant ID in participants.csv for counting users

def register_participant():

    if "participant_id" not in st.session_state:

        st.session_state["participant_id"] = str(uuid.uuid4())

        df = pd.DataFrame(
            [[st.session_state["participant_id"]]],
            columns=["participant_id"]
        )

        try:
            df.to_csv(PARTICIPANTS_FILE, mode="a", header=False, index=False)

        except:
            df.to_csv(PARTICIPANTS_FILE, index=False)

# Save a participant's answer to responses.csv
# Each record stores participant ID, question number, and selected option
# Used later to calculate poll results and charts

def save_response(participant_id, question_id, answer):

    df = pd.DataFrame(
        [[participant_id, question_id, answer]],
        columns=["participant_id", "question_id", "answer"]
    )

    try:
        df.to_csv(RESPONSES_FILE, mode="a", header=False, index=False)

    except:
        df.to_csv(RESPONSES_FILE, index=False)

# Check if a participant has already answered the current question
# Prevents users from submitting multiple votes for the same question
# Returns True if the participant already answered, otherwise False

def has_answered(participant_id, question_id):

    try:
        df = pd.read_csv(RESPONSES_FILE)

        filtered = df[
            (df["participant_id"] == participant_id) &
            (df["question_id"] == question_id)
        ]

        return len(filtered) > 0

    except:
        return False

# Read participants.csv and count how many participants joined the poll
# Used in presenter screen to display live participant count
# Returns 0 if file does not exist yet

def get_participant_count():

    try:
        df = pd.read_csv(PARTICIPANTS_FILE)
        return len(df)

    except:
        return 0

# Read responses.csv and count votes for the current question
# Returns how many votes each option (A,B,C,D) received
# Used to build the live results chart

def get_results(question_id):

    try:
        df = pd.read_csv(RESPONSES_FILE)

        df = df[df["question_id"] == question_id] if "question_id" in df.columns else df

        counts = df["answer"].value_counts()

        return counts

    except:
        return {}

# Create a bar chart showing how many votes each option received
# Converts the vote counts into a dataframe and renders it using Altair
# Used in presenter screen for live poll visualization

def show_chart(counts):

    chart_df = pd.DataFrame({
        "option": counts.index,
        "votes": counts.values
    })

    chart = alt.Chart(chart_df).mark_bar().encode(
        x="option",
        y="votes"
    )

    st.altair_chart(chart, use_container_width=True)

# Generate and display a QR code for the participant join link
# Participants scan this QR to open the poll on their device
# Used on the presenter landing screen

import io
def generate_qr(url):
        qr = qrcode.make(url)

        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)

        st.image(buf)
    
# Read URL query parameters to determine which screen to show
# mode=presenter → presenter control screen
# mode=participant → participant voting screen

params = st.query_params

if "mode" in params:
    mode = params["mode"]
else:
    mode = "presenter"

# Display the presenter landing page
# Shows QR code for participants, participant count, and Start Poll button

def presenter_landing():

    st_autorefresh(interval=1000)
    st.title("Live Poll")

    participant_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

    st.write("Scan this QR code to join the poll")

    generate_qr(participant_url)

    count = get_participant_count()

    st.metric("Participants Joined", count)

    if st.button("Start Poll"):
            state = load_state()
            state["poll_started"] = True
            save_state(state)

            st.rerun()
# Participant entry screen
# Registers the participant and shows waiting screen until poll starts

def participant_screen():
    
    st_autorefresh(interval=2000)
    register_participant()

    state = load_state()

    if not state["poll_started"]:

        st.title("Waiting for the poll to start")

        st.write("Please wait for the presenter to begin the poll.")

        return

    q_index = state["current_question"]

    q = questions[q_index]

    st.title(q["question"])

    options = ["A","B","C","D"]

    for opt in options:

        if st.button(q[opt]):

            pid = st.session_state["participant_id"]

            if not has_answered(pid, q_index):

                save_response(pid, q_index, opt)

                st.success("Answer submitted")

# Presenter view during the poll
# Shows the current question and refreshes automatically to update results
# Uses auto-refresh so the chart updates when new votes come in

def presenter_poll():


    st_autorefresh(interval=2000)
    
    state = load_state()
    
    questions = load_questions()
    
    q_index = state["current_question"]
    
    q = questions[q_index]
    
    st.title(q["question"])

# Get the vote counts for the current question
# If responses exist, display the results chart

    counts = get_results(q_index)
    
    if len(counts) > 0:
        show_chart(counts)
    
    # Presenter controls to move between questions or restart the poll
    # Updates poll_state.json and refreshes the app
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Previous"):
            state["current_question"] -= 1
            save_state(state)
            st.rerun()
    
    with col2:
        if st.button("Next"):
            state["current_question"] += 1
            save_state(state)
            st.rerun()
    
    with col3:
        if st.button("Restart"):
            state["current_question"] = 0
            state["poll_started"] = False
            save_state(state)
    
        open(RESPONSES_FILE, "w").close()
        open(PARTICIPANTS_FILE, "w").close()
        
        st.rerun()

# Main control logic of the application
# Decides whether to show presenter view or participant view
# Also checks if the poll has started

state = load_state()

if mode == "participant":
    participant_screen()

else:
    if not state["poll_started"]:
        presenter_landing()
    else:
        presenter_poll()








