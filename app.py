import streamlit as st
import time
from google import genai
from google.genai import types
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Database Connection
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

Base.metadata.create_all(engine)

# App UI
st.title("⚡ SDR Intelligence Engine")
user_transcript = st.text_area("Call Transcript", height=200)

if st.button("Analyze & Save"):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # AI logic
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=f"Analyze this. Return first line as 'OBJECTION: [short objection]'. Then provide analysis.\n\n{user_transcript}"
    )
    
    # Parse Objection
    ai_text = response.text
    objection = "Not specified"
    if "OBJECTION:" in ai_text:
        objection = ai_text.split("OBJECTION:")[1].split("\n")[0].strip()
    
    # Save to DB
    db = SessionLocal()
    new_call = CallLog(transcript=user_transcript, analysis=ai_text, primary_objection=objection)
    db.add(new_call)
    db.commit()
    db.close()
    
    st.markdown(ai_text)
    st.success("Saved to memory!")

# History Tab
if st.checkbox("Show History"):
    db = SessionLocal()
    history = db.query(CallLog).order_by(CallLog.timestamp.desc()).all()
    for entry in history:
        st.write(f"**Obj:** {entry.primary_objection} | **Time:** {entry.timestamp}")
    db.close()
