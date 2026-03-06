import streamlit as st
import json
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# --- CONFIGURATION (SECURE) ---
# ==========================================
# Fetch the API key securely from Streamlit Secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    st.error("GROQ_API_KEY is missing! Please add it to your Streamlit Secrets in the Advanced Settings.")
    st.stop()

# ==========================================
# --- STATE MANAGEMENT (The Agent's Memory) ---
# ==========================================
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None
if "rejection_count" not in st.session_state:
    st.session_state.rejection_count = 0
if "brief" not in st.session_state:
    st.session_state.brief = ""

# ==========================================
# --- THE AGENT'S BRAIN (Groq) ---
# ==========================================
def generate_campaign_assets(brief):
    """Uses Groq to generate strategy, subject, and body in JSON format."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        retry_context = ""
        if st.session_state.rejection_count > 0:
            retry_context = f"WARNING: The human manager REJECTED your last {st.session_state.rejection_count} draft(s). You MUST change your strategy, tone, and text completely."

        system_prompt = f"""
        You are an autonomous AI Marketing Agent. 
        Your job is to read a campaign brief and generate email content.
        
        {retry_context}
        
        STRICT RULES:
        1. You must decide whether to use emojis in the body, and where to put them.
        2. You must use markdown for font variations (like **bold** or *italics*) in the body.
        3. The subject line must be text only (no emojis).
        
        You MUST respond with ONLY a valid JSON object in this exact format:
        {{
            "strategy_reasoning": "A 1-sentence explanation of why you chose this tone.",
            "subject_line": "The email subject",
            "email_body": "The full email body formatting."
        }}
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the brief: {brief}"}
            ],
            temperature=0.8, 
            response_format={"type": "json_object"} 
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# --- THE EMAIL SENDER (Gmail) ---
# ==========================================
def send_real_gmail(sender_email, app_password, recipient_email, subject, email_body):
    """Sends a real email using Gmail's SMTP server with user-provided credentials."""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach the body as plain text
        msg.attach(MIMEText(email_body, 'plain'))

        # Connect to Gmail Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        
        # Login and Send
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# --- STREAMLIT UI ---
# ==========================================
st.set_page_config(page_title="AI Email Sender", layout="centered")
st.title("🤖 Personal AI Email Agent")

# ------------------------------------------
# STAGE 1: INPUT
# ------------------------------------------
if st.session_state.stage == "input":
    st.markdown("### Step 1: Configure Details & Tell the AI what to write")
    
    # Input fields for Credentials & Recipient
    with st.container(border=True):
        st.markdown("**Email Configuration**")
        col1, col2 = st.columns(2)
        with col1:
            sender_email = st.text_input("Your Gmail ID:", placeholder="you@gmail.com")
            app_password = st.text_input("Your App Password:", type="password", help="16-character app password with no spaces.")
        with col2:
            recipient_email = st.text_input("Recipient's Email:", placeholder="friend@example.com")
            
    brief = st.text_area("Email Instructions:", 
                         value="Write an email inviting my friend to a weekend hackathon. Make it sound exciting and mention there will be free pizza.", 
                         height=100)
    
    if st.button("Generate First Draft", type="primary"):
        # Basic validation to ensure fields aren't empty
        if not sender_email or not app_password or not recipient_email or not brief:
            st.error("Please fill in your Gmail ID, App Password, Recipient Email, and Instructions to continue.")
        else:
            with st.spinner("Agent is reasoning and writing..."):
                # Save inputs to session state so they persist to the next stages
                st.session_state.sender_email = sender_email
                st.session_state.app_password = app_password
                st.session_state.recipient_email = recipient_email
                st.session_state.brief = brief
                
                st.session_state.generated_data = generate_campaign_assets(brief)
                st.session_state.stage = "review"
                st.rerun()

# ------------------------------------------
# STAGE 2: REVIEW (APPROVE / REJECT)
# ------------------------------------------
elif st.session_state.stage == "review":
    st.markdown("### Step 2: Human Review")
    
    recipient = st.session_state.recipient_email
    st.warning(f"Review the agent's draft before sending to **{recipient}**.")
    
    result = st.session_state.generated_data
    
    if "error" in result:
        st.error(f"An error occurred: {result['error']}")
        if st.button("Try Again"):
            st.session_state.stage = "input"
            st.rerun()
    else:
        st.info(f"**🧠 Agent's Strategy:** {result.get('strategy_reasoning')}")
        st.write(f"**📧 Subject:** {result.get('subject_line')}")
        with st.container(border=True):
            st.markdown(result.get('email_body'))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ APPROVE & Send Email", use_container_width=True):
                with st.spinner("Sending real email via Gmail..."):
                    status = send_real_gmail(
                        st.session_state.sender_email,
                        st.session_state.app_password,
                        st.session_state.recipient_email,
                        result.get('subject_line'), 
                        result.get('email_body')
                    )
                    if status == "Success":
                        st.session_state.stage = "approved"
                        st.rerun()
                    else:
                        st.error(f"Failed to send: {status}. Please double-check your App Password and Email.")
        with col2:
            if st.button("❌ REJECT & Rewrite", use_container_width=True):
                st.session_state.rejection_count += 1
                with st.spinner(f"Agent is rewriting... (Attempt {st.session_state.rejection_count + 1})"):
                    st.session_state.generated_data = generate_campaign_assets(st.session_state.brief)
                st.rerun()

# ------------------------------------------
# STAGE 3: APPROVED (STOP)
# ------------------------------------------
elif st.session_state.stage == "approved":
    st.markdown("### Step 3: Success")
    st.success(f"✅ Email successfully sent to {st.session_state.recipient_email}!")
    
    if st.button("Write a New Email"):
        st.session_state.stage = "input"
        st.session_state.rejection_count = 0
        st.session_state.generated_data = None
        st.rerun()