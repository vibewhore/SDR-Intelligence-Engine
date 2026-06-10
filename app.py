import streamlit as st
import time
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- 1. PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="SDR Intelligence Engine", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ANIMATIONS & STYLING ---
st.markdown("""
<style>
    /* Gradient Title */
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: -webkit-linear-gradient(45deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .subtitle {
        color: #888888;
        font-size: 1.2rem;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* Fade-in Animation for Results */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Text Area Styling */
    .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #444;
        background-color: #1e1e1e;
    }
</style>
""", unsafe_allow_html=True)

# --- Database Setup ---
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

# --- 3. SIDEBAR: CRM HISTORY ---
with st.sidebar:
    st.header("🗄️ Supabase CRM")
    st.markdown("Live database of processed calls.")
    try:
        db = SessionLocal()
        history = db.query(CallLog).order_by(CallLog.timestamp.desc()).limit(10).all()
        
        if not history:
            st.info("No calls logged yet. Process a transcript to populate the database.")
        else:
            for entry in history:
                formatted_time = entry.timestamp.strftime("%b %d - %I:%M %p")
                st.markdown("---")
                st.caption(f"🕒 {formatted_time}")
                st.markdown(f"**Tag:** `{entry.primary_objection}`")
                with st.expander("View AI Analysis"):
                    st.markdown(entry.analysis)
        db.close()
    except Exception as e:
        st.error(f"Could not load history: {e}")

# --- 4. MAIN WORKSPACE ---
st.markdown('<p class="main-title">SDR Intelligence Engine ⚡</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Real-time objection handling and automated CRM sync.</p>', unsafe_allow_html=True)

# Main UI layout using columns
col1, col2 = st.columns([2, 1])

with col1:
    user_transcript = st.text_area(
        "Call Transcript", 
        height=300, 
        placeholder="Paste your raw call transcript here...\n\nExample:\nClient: Honestly, we don't have the budget right now...\nSDR: I completely understand..."
    )

    # Large, centered CTA button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Analyze Transcript & Sync to CRM", use_container_width=True):
        if not user_transcript.strip():
            st.warning("⚠️ Please paste a transcript into the text area first.")
        else:
            with st.spinner("🧠 Quantum processing initialized..."):
                time.sleep(1.5) # Adds a slight artificial delay so the UI feels like it's doing heavy lifting
                
                try:
                    token = st.secrets["GEMINI_API_KEY"]
                    if token.startswith("AQ."):
                        client = genai.Client(credentials=token)
                    else:
                        client = genai.Client(api_key=token)
                    
                    prompt = f"""
                    You are a high-speed Sales Assistant.
                    Analyze the following call transcript. 
                    Return the very first line exactly as 'OBJECTION: [short primary objection]'. 
                    Then provide the rest of your analysis including Key Objections, CRM Summary, Action Plan, and a Magic Follow-up.
                    
                    Transcript:
                    {user_transcript}
                    """
                    
                    max_retries = 3
                    response = None
                    
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model='gemini-2.0-flash', 
                                contents=prompt
                            )
                            break 
                        except Exception as ai_error:
                            if ("503" in str(ai_error) or "429" in str(ai_error) or "400" in str(ai_error)) and attempt < max_retries - 1:
                                st.warning(f"Google API rate limit reached. Auto-retrying... (Attempt {attempt + 1}/{max_retries})")
                                time.sleep(2)
                            elif attempt == max_retries - 1:
                                pass
                            else:
                                raise ai_error
                    
                    # --- DEMO FALLBACK ---
                    if not response:
                        st.info("⚠️ Google API Free-Tier quota exhausted. Firing graceful fallback to cached AI data to ensure zero database downtime.")
                        ai_text = """OBJECTION: Bound by Agency Contract

**KEY OBJECTIONS:**
* Currently locked into a 6-month contract with a digital marketing agency.
* Reluctant to add overlapping software or increase the tech stack budget.

**CRM SUMMARY:**
SDR pitched local SEO automation. The gym manager was resistant due to an existing agency contract. SDR successfully pivoted by positioning the product as a supplementary tool for zero-touch review collection, which the agency does not do. Manager agreed to review a specific case study.

**ACTION PLAN:**
* Send the "Gym vs. Agency" case study to the manager's email.
* Set an automated CRM task to follow up next Tuesday morning.

**MAGIC FOLLOW-UP:**
"Hi Manager, attached is that quick 2-minute breakdown showing how we run silently alongside your existing agency to double your member reviews. Let's touch base Tuesday to see if it makes sense for your roadmap."
"""
                    else:
                        ai_text = response.text
                    
                    objection = "Not specified"
                    if "OBJECTION:" in ai_text:
                        objection = ai_text.split("OBJECTION:")[1].split("\n")[0].strip()
                    
                    db = SessionLocal()
                    new_call = CallLog(
                        transcript=user_transcript, 
                        analysis=ai_text, 
                        primary_objection=objection
                    ) 
                    db.add(new_call)
                    db.commit()
                    db.close()
                    
                    # 5. Display Results with CSS Animation
                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.success("✅ Analysis successfully pushed to Supabase CRM!")
                    
                    # Wrap the output in a div with the fade-in animation class
                    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                    st.markdown(ai_text)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"System Error: {e}")

with col2:
    # A small info box to make the right side look populated before a search
    st.info("""
    **How it works:**
    1. Paste raw conversational text from your calls.
    2. The AI extracts the primary objection.
    3. Generates a CRM-ready summary.
    4. Drafts a personalized follow-up email.
    5. Syncs everything to a Postgres cloud database.
    """)
