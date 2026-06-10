import streamlit as st
import time
from google import genai
from google.genai import types
from google.genai.errors import ClientError

# 1. UI Configuration
st.set_page_config(page_title="SDR Intelligence Engine", page_icon="⚡", layout="centered")
st.title("⚡ SDR Intelligence Engine")
st.markdown("Paste your transcript to generate instant sales insights.")

# 2. User Input
user_transcript = st.text_area("Call Transcript", height=250, placeholder="Paste call transcript here...")

# 3. Processing Logic
if st.button("Analyze Call"):
    if user_transcript.strip() == "":
        st.error("Please paste a transcript first.")
    else:
        with st.spinner("Analyzing call..."):
            try:
                # Initialize Client using Streamlit Secrets
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                
                # High-Speed, Concise System Instructions
                system_instruction = """
                You are a high-speed Sales Assistant. 
                Constraint: Be extremely brief. Use bullet points only. 
                Max 2 sentences per section. No filler language.
                
                Return:
                * **KEY OBJECTIONS:**
                * **COMPETITORS:**
                * **CRM SUMMARY:**
                * **ACTION PLAN:**
                * **MAGIC FOLLOW-UP:**
                """
                
                # Retry Logic (Exponential Backoff for 429/503 errors)
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.5-flash',
                            contents=user_transcript,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.1,
                            )
                        )
                        
                        st.markdown("---")
                        st.markdown(response.text)
                        break # Exit loop on success
                        
                    except ClientError as e:
                        if e.code in [429, 503] and attempt < max_attempts - 1:
                            wait_time = (attempt + 1) * 5
                            st.warning(f"Server busy or limit reached. Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            st.error(f"Failed after {max_attempts} attempts. Error: {e}")
                            break
                            
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
