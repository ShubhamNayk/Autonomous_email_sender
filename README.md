# 🤖 Autonomous Email Sender — AI Email Agent

An AI-powered email assistant that writes and sends professional emails for you. Just describe what you want to say — the AI handles the rest.

**Live App:** [Click here to open](https://autonomous-email-sender.streamlit.app)

---

## What It Does

1. You describe your email in plain English (e.g. *"Write a follow-up email to my client about the pending invoice"*)
2. AI generates a professional subject line and email body
3. You review the draft
4. One click sends it from your Gmail

---

## How to Use the Website

### Step 1 — Open the App
Go to the live link above. You will see a form with 4 fields.

### Step 2 — Fill in Your Details

| Field | What to Enter |
|---|---|
| **Your Gmail ID** | The Gmail address you want to send from (e.g. `you@gmail.com`) |
| **Your App Password** | A special 16-character password from Google (NOT your regular Gmail password) |
| **Recipient's Email** | The email address you want to send to |
| **What should the email say?** | Your instructions in plain English |

### Step 3 — Get Your Gmail App Password (One-time Setup)

> Regular Gmail password won't work. You need a Google **App Password**.

1. Go to your Google Account → [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under *"How you sign in to Google"*, click **2-Step Verification** (enable it if not already on)
4. Scroll down and click **App passwords**
5. Choose app: **Mail** → Choose device: **Windows Computer** (or any)
6. Click **Generate** — you'll get a 16-character password like `abcd efgh ijkl mnop`
7. Copy that password and paste it into the **App Password** field in the app

### Step 4 — Generate & Review
- Click **"Generate First Draft"**
- The AI will write a subject line and full email body
- Review it carefully

### Step 5 — Send or Start Over
- Click **✅ Send Email** to send it immediately
- Click **❌ Start Over** if you want to change anything

---

## Tech Stack

- **Frontend:** Streamlit
- **AI Model:** LLaMA 3.3 70B via [Groq API](https://groq.com)
- **Email:** Gmail SMTP

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/ShubhamNayk/Autonomous_email_sender.git
cd Autonomous_email_sender

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key
mkdir .streamlit
echo 'GROQ_API_KEY = "your_key_here"' > .streamlit/secrets.toml

# 4. Run the app
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Important Notes

- Your Gmail password and App Password are **never stored** — they are only used during the session to send the email
- The `.streamlit/secrets.toml` file is excluded from git via `.gitignore`
- Works only with **Gmail** accounts currently
