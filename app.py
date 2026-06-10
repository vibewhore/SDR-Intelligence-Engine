import streamlit as st
import time
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- Database Setup ---
# Connect to Supabase using the URL from Streamlit Secrets
engine = create_engine(st.secrets["DATABASE_URL"])
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Define the database table schema
class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True)
    transcript = Column(Text)
    analysis = Column(Text)
    primary_objection = Column(String(200))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# NOTE: Base.metadata.create_all(engine) is removed.
# The table is managed directly in Supabase to prevent cloud pooler errors.

# --- UI and App Logic ---
st.title("⚡ SDR Intelligence Engine")
st.write("Paste your transcript to generate instant sales insights.")

user_transcript = st.text_area("Call Transcript", height=200)

if st.button("Analyze & Save"):
    if not user_transcript.strip():
        st.warning("Please enter a transcript first.")
    else:
        with st.spinner("Analyzing call..."):
            try:
                # 1. Initialize AI Client 
                token = st.secrets["GEMINI_API_KEY"]
                if token.startswith("AQ."):
                    client = genai.Client(credentials=token)
                else:
                    client = genai.Client(api_key=token)
                
                # 2. Call AI with specific instructions
                prompt = f"""
                You are a high-speed Sales Assistant.
                Analyze the following call transcript. 
                Return the very first line exactly as 'OBJECTION: [short primary objection]'. 
                Then provide the rest of your analysis including Key Objections, CRM Summary, Action Plan, and a Magic Follow-up.
                
                Transcript:
                {user_transcript}
                """
                
                # --- THE PRO DEVELOPER RETRY LOOP ---
                max_retries = 3
                response = None
                
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.5-flash',
                            contents=prompt
                        )
                        break # If it works, break out of the retry loop
                    except Exception as ai_error:
                        if "503" in str(ai_error) and attempt < max_retries - 1:
                            st.warning(f"Google servers are currently busy. Retrying... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(3)
                        elif attempt == max_retries - 1:
                            # We ran out of retries, but we WON'T crash. We will pass to the fallback.
                            pass
                        else:
                            raise ai_error
                
                # --- THE DEMO FALLBACK ---
                if not response:
                    st.info("⚠️ Google's AI is currently overloaded. Using a cached demo response so you can still test the database and UI!")
                    ai_text = """OBJECTION: Budget and Complexity

**KEY OBJECTIONS:**
* Strict budget constraints; cannot afford new monthly subscriptions.
* Burned by complicated software in the past (Podium).

**CRM SUMMARY:**
SDR pitched zero-touch SEO automation. Rahul (Manager) is relying on word-of-mouth and is highly skeptical due to past experiences. Agreed to look at a case study demonstrating a 30% increase in reviews.

**ACTION PLAN:**
* Email case study to rahul@thecoffeehouse.in immediately.
* Call Thursday morning to follow up on the metrics.

**MAGIC FOLLOW-UP:**
"Hi Rahul, here is that 2-minute case study showing how we boost reviews without adding work to your plate. I'll call you Thursday morning to get your thoughts."
"""
                else:
                    ai_text = response.text
                
                # 3. Parse the Primary Objection
                objection = "Not specified"
                if "OBJECTION:" in ai_text:
                    objection = ai_text.split("OBJECTION:")[1].split("\n")[0].strip()
                
                # 4. Save to Database
                db = SessionLocal()
                new_call = CallLog(
                    transcript=user_transcript, 
                    analysis=ai_text, 
                    primary_objection=objection
                ) # <--- The parenthesis syntax fix is implemented here
                
                db.add(new_call)
                db.commit()
                db.close()
                
                # 5. Display Results
                st.success("Analysis complete and saved to
