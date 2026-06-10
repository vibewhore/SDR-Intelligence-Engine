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

# --- 3. SESSION STATE FOR LOGIN & CHATBOT ---
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
        st.markdown('<p class="subtitle" style="text-align: center;">Authorized Personnel Only</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin or sdr")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_button = st.form_submit_button("Authenticate ⚡", use_container_width=True)
            
            if submit_button:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True; st.session_state.role = "admin"; st.session_state.username = "Administrator"; st.rerun()
                elif username == "sdr" and password == "sdr123":
                    st.session_state.logged_in = True; st.session_state.role = "employee"; st.session_state.username = "SDR Team"; st.rerun()
                else:
                    st.error("❌ Access Denied: Invalid credentials.")
    st.stop()

# --- 5. MAIN APP (ONLY SHOWS IF LOGGED IN) ---
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

# Initialize Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown(f"### 👤 Welcome, {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    st.markdown("---")
    st.header("🗄️ Supabase CRM")
    
    if st.session_state.role == "admin":
        st.markdown("Live database of processed calls.")
        try:
            db = SessionLocal()
            history = db.query(CallLog).order_by(CallLog.timestamp.desc()).limit(10).all()
            if not history: st.info("No calls logged yet.")
            else:
                for entry in history:
                    st.markdown("---")
                    st.caption(f"🕒 {entry.timestamp.strftime('%b %d - %I:%M %p')}")
                    st.markdown(f"**Tag:** `{entry.primary_objection}`")
                    with st.expander("View AI Analysis"): st.markdown(entry.analysis)
            db.close()
        except Exception as e: st.error(f"Could not load history: {e}")
    else:
        st.warning("🔒 Database view is restricted to Administrators.")

# --- MAIN WORKSPACE ---
st.markdown('<p class="main-title">SDR Intelligence Engine ⚡</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time objection handling, CRM sync, and AI Strategy Coaching.</p>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    user_transcript = st.text_area("Call Transcript", height=250, placeholder="Paste your raw call transcript here...")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Analyze Transcript & Sync to CRM", use_container_width=True):
        if not user_transcript.strip():
            st.warning("⚠️ Please paste a transcript first.")
        else:
            with st.spinner("🧠 Quantum processing initialized via Groq..."):
                try:
                    # System Prompt for Groq (Meta Llama 3)
                    prompt = f"""
                    You are a high-speed Sales Assistant.
                    Analyze the following call transcript. 
                    Return the very first line exactly as 'OBJECTION: [short primary objection]'. 
                    Then provide the rest of your analysis including Key Objections, CRM Summary, Action Plan, and a Magic Follow-up.
                    
                    Transcript:
                    {user_transcript}
                    """
                    
                    # Groq API Call
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192", # Lightning fast Meta model
                    )
                    
                    ai_text = chat_completion.choices[0].message.content
                    
                    # Parse Objection
                    objection = "Not specified"
                    if "OBJECTION:" in ai_text:
                        objection = ai_text.split("OBJECTION:")[1].split("\n")[0].strip()
                    
                    # Save to Supabase
                    db = SessionLocal()
                    new_call = CallLog(transcript=user_transcript, analysis=ai_text, primary_objection=objection) 
                    db.add(new_call)
                    db.commit()
                    db.close()
                    
                    # Save analysis to session state so the chatbot can read it
                    st.session_state.current_analysis = ai_text
                    st.session_state.chat_history = [] # Clear previous chat history
                    
                    st.success("✅ Analysis successfully pushed to Supabase CRM!")
                    
                except Exception as e:
                    st.error(f"System Error: {e}")

    # Display Current Analysis (if it exists)
    if st.session_state.current_analysis:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 📊 AI Call Analysis")
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.markdown(st.session_state.current_analysis)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.info("""
    **How it works:**
    1. **Paste** a call transcript.
    2. **Groq Llama-3** parses objections instantly.
    3. **Supabase Postgres** securely syncs the log.
    4. **AI Coach** unlocks at the bottom to help you strategize next steps!
    """)

# --- 6. AI STRATEGY COACH CHATBOT (Only appears after analysis) ---
if st.session_state.current_analysis:
    st.markdown("---")
    st.markdown('<p class="main-title" style="font-size: 2.5rem;">🤖 Strategy Coach</p>', unsafe_allow_html=True)
    st.markdown("Ask the AI to draft a custom email, write a LinkedIn connection request, or roleplay the next call based on the analysis above.")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Box
    if user_prompt := st.chat_input("E.g., 'Draft a casual LinkedIn request for this prospect...'"):
        # Show user message
        st.chat_message("user").markdown(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})

        # Generate AI response using Groq
        with st.spinner("Thinking..."):
            try:
                # Give Groq the context of the current analysis, plus the user's new question
                system_context = f"You are an elite Sales Manager coaching an SDR. Here is the context of their last call: {st.session_state.current_analysis}"
                
                messages_for_api = [{"role": "system", "content": system_context}]
                # Add history so the bot remembers the conversation
                for msg in st.session_state.chat_history:
                    messages_for_api.append(msg)
                
                chat_completion = client.chat.completions.create(
                    messages=messages_for_api,
                    model="llama3-8b-8192",
                )
                
                bot_response = chat_completion.choices[0].message.content
                
                # Show bot response
                st.chat_message("assistant").markdown(bot_response)
                st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                
            except Exception as e:
                st.error(f"Chatbot Error: {e}")
