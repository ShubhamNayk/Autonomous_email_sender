import streamlit as st
import json
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# --- CONFIGURATION (SECURE) ---
# ==========================================
# This looks for the key in Streamlit Cloud "Advanced Settings > Secrets"
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("GROQ_API_KEY is missing! Check your Streamlit Secrets dashboard.")
    st.stop()

# ==========================================
# --- STATE MANAGEMENT ---
# ==========================================
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

# ==========================================
# --- THE AGENT'S BRAIN (Groq) ---
# ==========================================
def generate_email_content(brief):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        system_prompt = """
        You are an AI Email Assistant. Respond ONLY with a JSON object:
        {
            "subject": "The email subject",
            "body": "The full email body"
        }
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Instructions: {brief}"}
            ],
            response_format={"type": "json_object"} 
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# --- THE EMAIL SENDER ---
# ==========================================
def send_email(sender, password, recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = sender, recipient, subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# --- STREAMLIT UI ---
# ==========================================
st.set_page_config(page_title="AI Email Agent", layout="centered")
st.title("🤖 Personal AI Email Agent")

# --- STAGE 1: INPUT ---
if st.session_state.stage == "input":
    st.markdown("### Step 1: Configuration & Instructions")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            # We use 'key' to store these directly in session_state
            st.text_input("Your Gmail ID:", placeholder="you@gmail.com", key="sender_email")
            st.text_input("Your App Password:", type="password", key="app_password")
        with col2:
            st.text_input("Recipient's Email:", placeholder="friend@gmail.com", key="target_email")
            
    st.text_area("What should the email say?", placeholder="Write instructions here...", height=150, key="email_brief")
    
    if st.button("Generate First Draft", type="primary"):
        # We check the session_state keys directly to ensure we don't miss any data
        s_email = st.session_state.get("sender_email")
        s_pass = st.session_state.get("app_password")
        t_email = st.session_state.get("target_email")
        brief = st.session_state.get("email_brief")

        if not all([s_email, s_pass, t_email, brief]):
            st.error("❌ All fields are required. Please type and click outside the box before pressing Generate.")
        else:
            with st.spinner("AI is thinking..."):
                st.session_state.generated_data = generate_email_content(brief)
                st.session_state.stage = "review"
                st.rerun()

# --- STAGE 2: REVIEW ---
elif st.session_state.stage == "review":
    st.markdown("### Step 2: Review & Send")
    res = st.session_state.generated_data
    
    if "error" in res:
        st.error(f"AI Error: {res['error']}")
        if st.button("Try Again"):
            st.session_state.stage = "input"
            st.rerun()
    else:
        st.write(f"**To:** {st.session_state.target_email}")
        st.write(f"**Subject:** {res.get('subject')}")
        with st.container(border=True):
            st.markdown(res.get('body'))
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Send Email", use_container_width=True):
                with st.spinner("Sending..."):
                    status = send_email(
                        st.session_state.sender_email,
                        st.session_state.app_password,
                        st.session_state.target_email,
                        res.get('subject'),
                        res.get('body')
                    )
                    if status == "Success":
                        st.session_state.stage = "success"
                        st.rerun()
                    else:
                        st.error(status)
        with col_b:
            if st.button("❌ Start Over", use_container_width=True):
                st.session_state.stage = "input"
                st.rerun()

# --- STAGE 3: SUCCESS ---
elif st.session_state.stage == "success":
    st.balloons()
    st.success("✅ Email Sent Successfully!")
    if st.button("Write Another"):
        st.session_state.stage = "input"
        st.rerun()
