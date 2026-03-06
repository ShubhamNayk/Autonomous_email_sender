import streamlit as st
import json
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# --- CONFIGURATION (SECURE) ---
# ==========================================
# This looks for the key you pasted in Streamlit's "Advanced Settings > Secrets"
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("GROQ_API_KEY is missing! Please add it to your Streamlit Secrets in the Cloud Dashboard.")
    st.stop()

# ==========================================
# --- STATE MANAGEMENT ---
# ==========================================
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None
if "rejection_count" not in st.session_state:
    st.session_state.rejection_count = 0

# ==========================================
# --- THE AGENT'S BRAIN (Groq) ---
# ==========================================
def generate_campaign_assets(brief):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        retry_context = ""
        if st.session_state.rejection_count > 0:
            retry_context = f"WARNING: The human manager REJECTED your last {st.session_state.rejection_count} draft(s). You MUST change your strategy and text completely."

        system_prompt = f"""
        You are an AI Email Assistant. 
        Read the instructions and generate a subject and body.
        {retry_context}
        
        STRICT RULES:
        1. Use markdown for **bold** or *italics* in the body.
        2. The subject line must be text only.
        
        Respond ONLY with a JSON object:
        {{
            "strategy_reasoning": "Reason for tone.",
            "subject_line": "Subject",
            "email_body": "Body text"
        }}
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Instructions: {brief}"}
            ],
            temperature=0.8, 
            response_format={"type": "json_object"} 
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# --- THE EMAIL SENDER ---
# ==========================================
def send_real_gmail(sender, password, recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
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
        st.markdown("**Sender & Recipient Details**")
        col1, col2 = st.columns(2)
        with col1:
            u_email = st.text_input("Your Gmail ID:", placeholder="example@gmail.com", key="u_email")
            u_pass = st.text_input("Your App Password:", type="password", help="16-character code from Google Security.", key="u_pass")
        with col2:
            r_email = st.text_input("Recipient's Email:", placeholder="friend@gmail.com", key="r_email")
            
    u_brief = st.text_area("What should the email say?", placeholder="e.g. Invite my friend to coffee tomorrow at 4 PM.", height=150, key="u_brief")
    
    if st.button("Generate First Draft", type="primary"):
        # This check ensures all fields are captured correctly
        if not u_email or not u_pass or not r_email or not u_brief:
            st.error("❌ Please fill in ALL fields above before generating.")
        else:
            with st.spinner("AI is writing your email..."):
                st.session_state.sender_email = u_email
                st.session_state.app_password = u_pass
                st.session_state.recipient_email = r_email
                st.session_state.brief = u_brief
                
                st.session_state.generated_data = generate_campaign_assets(u_brief)
                st.session_state.stage = "review"
                st.rerun()

# --- STAGE 2: REVIEW ---
elif st.session_state.stage == "review":
    st.markdown("### Step 2: Review Draft")
    st.info(f"Draft for: **{st.session_state.recipient_email}**")
    
    res = st.session_state.generated_data
    if "error" in res:
        st.error(f"AI Error: {res['error']}")
        if st.button("Back to Start"):
            st.session_state.stage = "input"
            st.rerun()
    else:
        st.markdown(f"**Subject:** {res.get('subject_line')}")
        with st.container(border=True):
            st.markdown(res.get('email_body'))
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Send Email Now", use_container_width=True):
                with st.spinner("Sending..."):
                    status = send_real_gmail(
                        st.session_state.sender_email,
                        st.session_state.app_password,
                        st.session_state.recipient_email,
                        res.get('subject_line'),
                        res.get('email_body')
                    )
                    if status == "Success":
                        st.session_state.stage = "success"
                        st.rerun()
                    else:
                        st.error(f"Login Failed: {status}")
        with col_b:
            if st.button("❌ Rewrite Email", use_container_width=True):
                st.session_state.rejection_count += 1
                st.session_state.generated_data = generate_campaign_assets(st.session_state.brief)
                st.rerun()

# --- STAGE 3: SUCCESS ---
elif st.session_state.stage == "success":
    st.balloons()
    st.success(f"Email sent successfully to {st.session_state.recipient_email}!")
    if st.button("Write Another Email"):
        st.session_state.stage = "input"
        st.session_state.rejection_count = 0
        st.rerun()
