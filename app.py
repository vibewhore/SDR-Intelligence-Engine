import streamlit as st
import re
from groq import Groq
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="SDR Intelligence Engine", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at 10% 20%, #0a0e17 0%, #000000 100%); color: #e0e6ed; }
    .main-title { font-size: 3.5rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION & DB ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_analysis" not in st.session_state: st.session_state.current_analysis = None

engine = create_engine(st.secrets["DATABASE_URL"])
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True)
    transcript = Column(Text)
    analysis = Column(Text)
    primary_objection = Column(String(200))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. AUTH & UI ---
if not st.session_state.logged_in:
    with st.columns([1, 2, 1])[1]:
        st.markdown('<p class="main-title" style="text-align: center;">System Access</p>', unsafe_allow_html=True)
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if (user == "admin" and pwd == "admin123") or (user == "sdr" and pwd == "sdr123"):
                st.session_state.logged_in = True
                st.session_state.role = "admin" if user == "admin" else "employee"
                st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- 4. APP LOGIC ---
st.markdown('<p class="main-title">SDR Intelligence Engine ⚡</p>', unsafe_allow_html=True)
user_transcript = st.text_area("Paste Transcript", height=200)

if st.button("Analyze Transcript"):
    with st.spinner("Processing..."):
        prompt = f"Analyze: {user_transcript}. Return with 'OBJECTION: [short summary]' then full analysis."
        resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        ai_text = resp.choices[0].message.content
        
        # Robust Parsing
        match = re.search(r'OBJECTION:\s*(.*)', ai_text, re.IGNORECASE)
        objection = match.group(1).replace("*", "").strip() if match else "Not specified"
        
        db = SessionLocal()
        db.add(CallLog(transcript=user_transcript, analysis=ai_text, primary_objection=objection))
        db.commit()
        db.close()
        
        st.session_state.current_analysis = ai_text
        st.session_state.chat_history = []
        st.rerun()

if st.session_state.current_analysis:
    st.markdown("---")
    st.markdown(st.session_state.current_analysis)
    
    st.markdown("### 🤖 Strategy Coach")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
    if prompt := st.chat_input("Ask for advice..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                messages = [{"role": "system", "content": f"Context: {st.session_state.current_analysis}"}] + st.session_state.chat_history
                resp = client.chat.completions.create(messages=messages, model="llama-3.3-70b-versatile")
                reply = resp.choices[0].message.content
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
