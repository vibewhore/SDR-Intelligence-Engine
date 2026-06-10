import streamlit as st
import time
from google import genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

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
                        # If it's a 503 error and we haven't run out of tries, wait and retry
                        if "503" in str(ai_error) and attempt < max_retries - 1:
                            st.warning(f"Google servers are currently busy. Retrying in 3 seconds... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(3)
                        else:
                            # If it's a different error, or we are out of tries, crash normally
                            raise ai_error
                
                # Ensure we actually got a response before proceeding
                if not response:
                    st.error("Failed to get a response from the AI after multiple attempts.")
                    st.stop()

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
                )
                db.add(new_call)
                db.commit()
                db.close()
                
                # 5. Display Results
                st.success("Analysis complete and saved to memory!")
                st.markdown(ai_text)
                
            except Exception as e:
                st.error(f"An API or Database error occurred: {e}")

# --- History Section ---
st.markdown("---")
if st.checkbox("Show History"):
    st.subheader("Call Logs")
    try:
        db = SessionLocal()
        history = db.query(CallLog).order_by(CallLog.timestamp.desc()).all()
        
        if not history:
            st.info("No calls logged yet. Analyze a transcript to see it here!")
        else:
            for entry in history:
                formatted_time = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(f"**Date:** {formatted_time} | **Objection:** {entry.primary_objection}")
                
                with st.expander("View Full Analysis"):
                    st.markdown(entry.analysis)
        db.close()
    except Exception as e:
        st.error(f"Could not load history: {e}")
