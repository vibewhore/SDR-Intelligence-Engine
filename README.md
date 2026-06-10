# ⚡ SDR Intelligence Engine

An enterprise-grade, AI-powered sales enablement platform designed to streamline call analysis, automate CRM synchronization, and provide real-time strategic coaching for Sales Development Representatives (SDRs).

## 🚀 The Problem
Sales teams often struggle with inconsistent objection handling, manual CRM data entry, and a lack of post-call strategy, leading to lost leads and inefficient follow-ups.

## 💡 The Solution
The **SDR Intelligence Engine** acts as an autonomous sales co-pilot. It transforms raw call transcripts into structured CRM insights, identifies primary customer objections, and provides an interactive "Strategy Coach" to help SDRs plan their next move.

## 🛠️ Tech Stack
- **Frontend:** Streamlit (Custom CSS/Glassmorphism UI)
- **AI Engine:** Groq API (Meta Llama-3.3-70b-versatile) for sub-second, high-performance inference.
- **Database:** Supabase (PostgreSQL)
- **Backend/ORM:** SQLAlchemy for secure database interaction.
- **Infrastructure:** Hosted & deployed via Streamlit Cloud.

## 🔑 Key Features
- **Intelligent Objection Detection:** Uses Regex-powered parsing to automatically extract and tag customer objections from unstructured transcripts.
- **Role-Based Access Control (RBAC):** Enterprise-level security separating SDRs (data entry) from Admins (CRM oversight).
- **Interactive AI Strategy Coach:** Context-aware chatbot that uses call analysis to help SDRs draft emails, prepare for follow-ups, and roleplay objections.
- **Graceful Error Handling:** Engineered for resilience; ensures data integrity even if API rate limits are encountered.

## 📊 How It Works
1. **Analyze:** Paste raw conversational text. The AI extracts the primary objection and generates a full CRM-ready summary.
2. **Sync:** Analysis is automatically committed to a secure Supabase Postgres database.
3. **Strategize:** The AI Coach activates, utilizing the current call context to provide personalized coaching and follow-up templates.

## 👤 Login Credentials (For Demo)
* **Admin:** `admin` / `admin123`
* **SDR:** `sdr` / `sdr123`

---
*Built by Vibhor Sharma | www.linkedin.com/in/vibhor-sharma-6a1a09367
