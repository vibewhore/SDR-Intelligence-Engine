import streamlit as st
import time
from groq import Groq
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SDR Intelligence Engine", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. ZETTA JOULE INSPIRED CSS ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at 10% 20%, #0a0e17 0%, #000000 100%); color: #e0e6ed; }
    .main-title {
        font-size: 3.5rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; padding-bottom: 0px; letter-spacing: -1px;
    }
    .subtitle { color: #8da2b5; font-size: 1.1rem; margin-top: -10px; margin-bottom: 30px; font-weight: 300; }
    .stButton>button {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%); color: #000000 !important; border: none;
        border-radius: 8px; font-weight: 700; font-size: 1.1rem; padding: 0.6rem 1.5rem; box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3); transition: all 0.3s ease;
    }
    .stButton>button:hover { box-shadow: 0 6px 25px rgba(0, 242, 254, 0.6); transform: translateY(-2px); }
    .stTextArea textarea, .stTextInput input {
        background: rgba(16, 22, 35, 0.7) !important; border: 1px solid rgba(79, 172, 254, 0.2) !important;
        border-radius: 10px; color: #e0e6ed !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { border: 1px solid #00f2fe !important; box-shadow: 0 0 12px rgba(0, 242, 254, 0.2) !important; }
    [data-testid="stSidebar"] { background-color: #05080f !important; border-right: 1px solid rgba(79, 172, 254, 0.1); }
    .fade-in { animation: fadeIn 0.8s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "role" not in st.session_state: st.session_state.role = None
if "username" not in st.session_state: st.session_state.username = ""
if "current_analysis" not in st.session_state: st.session_state.current_analysis = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- 4. LOGIN SCREEN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="main-title" style="text-align: center;">System Access</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or sdr")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Authenticate ⚡", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True; st.session_state.role = "admin"; st.session_state.username = "Administrator"; st.rerun()
                elif username == "sdr" and password == "sdr123":
                    st.session_state.logged_in = True; st.session_state.role = "employee"; st.session_state.username = "SDR Team"; st.rerun()
                else:
                    st.error("❌ Access Denied")
    st.stop()

# --- 5. MAIN APP ---
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

with st.sidebar:
    st.markdown(f"### 👤 Welcome, {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.markdown("---")
    st.header("🗄️ Supabase CRM")
    if st.session_state.role == "admin":
        try:
            db = SessionLocal()
            history = db.query(CallLog).order_by(CallLog.timestamp.desc()).limit(10).all()
            for entry in history:
                st.markdown("---")
                st.markdown(f"**Tag:** `{entry.primary_objection}`")
                with st.expander("View AI Analysis"): st.markdown(entry.analysis)
            db.close()
        except: st.error("Database connection issue.")
    else:
        st.warning("🔒 Database view restricted.")

st.markdown('<p class="main-title">SDR Intelligence Engine ⚡</p>', unsafe_allow_html=True)

user_transcript = st.text_area("Call Transcript", height=250)

if st.button("🚀 Analyze Transcript & Sync to CRM", use_container_width=True):
    if not user_transcript.strip():
        st.warning("⚠️ Please paste a transcript first.")
    else:
        with st.spinner("🧠 Quantum processing via Groq..."):
            try:
                prompt = f"Analyze this sales transcript: {user_transcript}. Return with 'OBJECTION: [short summary]' followed by full analysis."
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile", # <--- UPGRADED STABLE MODEL
                )
                ai_text = chat_completion.choices[0].message.content
                objection = ai_text.split("OBJECTION:")[1].split("\n")[0].strip() if "OBJECTION:" in ai_text else "Not specified"
                
                db = SessionLocal()
                db.add(CallLog(transcript=user_transcript, analysis=ai_text, primary_objection=objection))
                db.commit()
                db.close()
                
                st.session_state.current_analysis = ai_text
                st.success("✅ Logged to CRM!")
            except Exception as e:
                st.error(f"System Error: {e}")

if st.session_state.current_analysis:
    st.markdown("---")
    st.markdown(st.session_state.current_analysis)
    
    st.markdown("### 🤖 Strategy Coach")
    if user_prompt := st.chat_input("Ask for email drafts or roleplay..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.spinner("Thinking..."):
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": f"Context: {st.session_state.current_analysis}"}] + st.session_state.chat_history,
                model="llama-3.3-70b-versatile", # <--- UPGRADED STABLE MODEL
            )
            bot_response = chat_completion.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            st.rerun()
