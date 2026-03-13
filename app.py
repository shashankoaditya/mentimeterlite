import streamlit as st
import qrcode
from io import BytesIO

st.set_page_config(page_title="Live Poll", layout="centered")

# read URL parameters
params = st.query_params
mode = params.get("mode", "home")

# -------------------------
# LANDING PAGE
# -------------------------

if mode == "home":

    st.title("📊 Live Poll")

    st.subheader("Scan the QR Code to Join")

    poll_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

    qr = qrcode.make(poll_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    st.image(buffer.getvalue(), width=300)

    st.write("Use your phone to scan and join the poll")

# -------------------------
# PARTICIPANT PAGE
# -------------------------

elif mode == "participant":

    st.title("Vote")

    st.subheader("What does AI stand for?")

    answer = st.radio(
        "Choose",
        [
        "Artificial Intelligence",
        "Automated Internet",
        "Advanced Interface",
        "Algorithmic Input"
        ]
    )

    if st.button("Submit"):
        st.success("Vote submitted")
