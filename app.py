import streamlit as st
import qrcode
from io import BytesIO

st.set_page_config(page_title="Live Poll", layout="centered")

st.title("📊 Live Poll")

st.subheader("Scan the QR Code to Join")

# your deployed app URL
poll_url = "https://mentimeterlite-dxem3jgznxqheyg4ncjcus.streamlit.app/?mode=participant"

qr = qrcode.make(poll_url)

buffer = BytesIO()
qr.save(buffer, format="PNG")

st.image(buffer.getvalue(), width=300)

st.write("Use your phone to scan and join the poll.")
