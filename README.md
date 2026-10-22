# Infosys Springboard Internship 7.0 (Batch 4) — Milestone 1
## Secure User Authentication & Access Management Module
**Tech Stack:** Python 3.11 · Streamlit · JSON Web Tokens (PyJWT) · SQLite3 · bcrypt · Gmail SMTP (STARTTLS) · ngrok · Google Colab Secrets

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io/)
[![JWT](https://img.shields.io/badge/JWT-HS256-black.svg)](https://jwt.io/)
[![Security](https://img.shields.io/badge/Security-bcrypt%20%2B%20Colab%20Secrets-brightgreen.svg)](#security-architecture)
[![License](https://img.shields.io/badge/Status-Completed%20%26%20Verified-success.svg)](#final-checklist)

---

## 📖 Executive Summary
Milestone 1 is the foundational security layer for the **TEST** project. It delivers an enterprise-grade, multi-role user authentication and access control system built in **Python** and **Streamlit**. 

The system implements state-of-the-art authentication paradigms including:
- **Cryptographic JWT (JSON Web Tokens)** session handling with active signature and expiry verification.
- **Strong Hashing (bcrypt)** for credential protection with automated salting.
- **Dual-Route Self-Service Password Recovery** utilizing Security Questions and real-time **Gmail OTP verification**.
- **Role-Based Access Control (RBAC)** providing distinct protected views for Standard Users and System Administrators, adhering strictly to audit compliance standards (passwords and hashes are entirely redacted in admin views).
- **Zero-Credential Hardcoding Policy** integrated with Google Colab Secrets and environment variable loaders.

---

## 🏛️ System Architecture

```
                                 +-----------------------------------+
                                 |         Streamlit Web UI          |
                                 | (Glassmorphism & Branded Theme)   |
                                 +-----------------+-----------------+
                                                   |
                     +-----------------------------+-----------------------------+
                     |                             |                             |
                     v                             v                             v
           +------------------+          +------------------+          +------------------+
           |   Login & Auth   |          |      Signup      |          | Forgot Password  |
           |   (Generic Err)  |          | (Field Validate) |          | (SQ / Gmail OTP) |
           +--------+---------+          +--------+---------+          +--------+---------+
                    |                             |                             |
                    +-----------------------------+-----------------------------+
                                                  |
                                                  v
                                    +---------------------------+
                                    |     Security Pipeline     |
                                    | - Email Rule: ab@cd.ef    |
                                    | - Pwd Regex (Complexity)  |
                                    | - bcrypt Salt & Hash      |
                                    | - HS256 JWT Tokenization  |
                                    +-------------+-------------+
                                                  |
                     +----------------------------+----------------------------+
                     |                                                         |
                     v                                                         v
        +-------------------------+                               +-------------------------+
        |  Protected User Dash    |                               |  Dedicated Admin Portal |
        | - Verified JWT Claims   |                               | - Registered User Audit |
        | - Session Expiration    |                               | - Passwords Redacted    |
        | - Dynamic Milestone Log |                               | - Filter & Search Tool  |
        +-------------------------+                               +-------------------------+
```

---

## 🚀 Key Features

### 1. Robust Registration (Signup)
- **Mandatory Fields:** Username, Email, Password, Confirm Password, Security Question dropdown, and Security Answer.
- **Uniqueness Check:** Enforces unique usernames and emails in SQLite, rejecting collisions with informative error banners.
- **Email Validation Rule:** Matches strict pattern requirement: at least 2 letters before the `@`, at least 2 letters between the `@` and the dot, and at least 2 letters after the final dot (e.g. `ab@cd.ef`).
- **Password Complexity Engine:** Requires minimum 8 characters, at least 1 uppercase letter (`A-Z`), at least 1 lowercase letter (`a-z`), at least 1 number (`0-9`), at least 1 special symbol (`!@#$%^&*()_+-=[]{}|;:,.<>?`), and exact match with Confirm Password.
- **Storage:** Passwords hashed with `bcrypt` (12 rounds). Security answers are normalized and hashed using SHA-256 to ensure complete privacy.

### 2. Secure Login with Single Generic Error
- Supports login via either **Username** or **Email Address**.
- Mandatory field validation.
- **Defense Against User Enumeration:** If authentication fails, the application outputs a single generic error: `"Invalid username/email or password"`, preventing attackers from determining whether an account exists.
- **Session Issuance:** On valid credentials, generates a signed JWT session token with user claims and expiration timestamp.

### 3. Dual-Route Password Recovery (Forgot Password)
- **Route 1: Security Question Route**
  - Enter username -> Fetches registered question.
  - Case-insensitive comparison against stored security answer hash.
  - Sets new password validated against the full password complexity rules.
- **Route 2: Gmail OTP Route**
  - Enter registered email -> Generates a cryptographically random 6-digit numeric OTP.
  - Dispatches branded HTML + Plaintext email via Google SMTP (`smtp.gmail.com:587`, STARTTLS).
  - Time-bounded OTP validation (10-minute expiry window, single-use invalidation).
  - Updates password in SQLite and redirects to Login.

### 4. Protected User Dashboard
- Accessible only when a valid, non-expired JWT session token is present.
- Displays:
  - Welcome greeting with authenticated username and email.
  - Active session countdown and token expiration timestamp.
  - Live decoded JWT payload inspector (`sub`, `email`, `role`, `iat`, `exp`).
  - Milestone 1 completion checklist.
  - One-click **Logout** button that purges session state and terminates the JWT session.

### 5. Dedicated Admin Portal & Dashboard
- Separate administrative login gate using credentials configured directly in code / Colab Secrets (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).
- Protected with Administrator JWT token.
- **Strict Compliance (Step 11):** Passwords and password hashes are strictly redacted and NEVER fetched or rendered on screen.
- Real-time directory of all registered users with registration timestamps, security question selection, search/filter bar, and system metrics.

---

## 🗂️ Project Directory Structure

```
Milestone1/
├── app.py                           # Main multi-page Streamlit application with custom branding
├── auth.py                          # JWT tokenization, bcrypt hashing, field validation engine
├── database.py                      # SQLite3 database manager, users schema, OTP verification
├── mailer.py                        # Gmail SMTP email delivery with HTML template & fallback
├── config.py                        # Google Colab Secrets & local environment variable loader
├── requirements.txt                 # Project dependencies
├── .env.example                     # Local environment configuration template
├── Milestone1_Authentication.ipynb  # Complete Google Colab notebook (cleaned, ready to run)
├── README.md                        # Project documentation (this file)
└── screenshots/                     # Verification screenshots
    ├── 01_login_page.png
    ├── 02_signup_page.png
    ├── 03_forgot_password_security_question.png
    ├── 04_forgot_password_otp.png
    ├── 05_otp_email.png
    ├── 06_user_dashboard.png
    └── 07_admin_dashboard.png
```

---

## 🔑 Colab Secrets Configuration (Step 4, 5, 6)

In Google Colab, never hard-code credentials. Configure them under the **Secrets (Key Icon)** tab in the left sidebar:

### Official Google Gmail API (OAuth 2.0 via HTTPS Port 443 — Bypasses Outbound SMTP Block)

| Secret Name | Category | Description / Instructions |
|---|---|---|
| `GMAIL_CLIENT_ID` | Gmail API (OAuth 2.0) | OAuth 2.0 Client ID from Google Cloud Console |
| `GMAIL_CLIENT_SECRET` | Gmail API (OAuth 2.0) | OAuth 2.0 Client Secret from Google Cloud Console |
| `GMAIL_REFRESH_TOKEN` | Gmail API (OAuth 2.0) | Long-lived OAuth 2.0 Refresh Token with `gmail.send` scope |
| `EMAIL_ADDRESS` | Gmail API | Your Gmail address (used in the email 'From' header) |
| `JWT_SECRET` | Security / Session | A secure random string for signing JWT tokens (e.g. `your_random_secret_key`) |
| `NGROK_AUTHTOKEN` | Tunneling | Your personal authtoken from [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) |
| `ADMIN_USERNAME` | Admin Portal | *(Optional)* Custom administrator username (defaults to `admin`) |
| `ADMIN_PASSWORD` | Admin Portal | *(Optional)* Custom administrator password configured via Secrets/env |

> ⚠️ **Important:** Enable the **Notebook access** toggle for each secret in Google Colab so the Python runtime can read them.

---

## 💻 How to Run the Application

### Option A: Running on Google Colab (Recommended)
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **File -> Upload notebook** and select `Milestone1_Authentication.ipynb`.
3. Add the 4 secrets under the **Secrets** icon on the left.
4. Run all cells from top to bottom.
5. In Step 3, the notebook will output a live public URL:
   ```
   🎉 STREAMLIT APP IS PUBLICLY LIVE AT:
   👉 https://xxxx-xx-xx-xx.ngrok-free.app
   ```
6. Click the link to interact with the full web app in your browser!

### Option B: Running Locally (Windows / macOS / Linux)
1. Clone or navigate to the repository directory:
   ```bash
   cd c:\Users\aadia\OneDrive\Desktop\Infosys_Agentic_AI\Milestone1
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your Gmail and ngrok details:
   ```bash
   cp .env.example .env
   ```
5. Launch the Streamlit application:
   ```bash
   streamlit run app.py
   ```
6. Open `http://localhost:8501` in your browser.

---

## 📸 Screenshots & Verification (Step 12)

### 1. User Login Page
Displays mandatory fields, clean corporate navigation, and generic failure error protection.
![User Login](screenshots/01_login_page.png)

---

### 2. New User Registration (Signup Page)
Validates mandatory inputs, unique usernames, `ab@cd.ef` email structure, and 5-point password complexity.
![Signup Page](screenshots/02_signup_page.png)

---

### 3. Password Recovery — Route 1: Security Question
Verifies the user-configured security question and answer before authorizing password update.
![Forgot Password Security Question](screenshots/03_forgot_password_security_question.png)

---

### 4. Password Recovery — Route 2: Gmail OTP
Generates a 6-digit numeric OTP with 10-minute validity and confirms identity prior to password reset.
![Forgot Password OTP](screenshots/04_forgot_password_otp.png)

---

### 5. Automated Gmail OTP Notification Email
Real-time branded security email dispatched via Gmail SMTP (`smtp.gmail.com:587`, STARTTLS).
![Gmail OTP Notification](screenshots/05_otp_email.png)

---

### 6. Protected User Dashboard
Accessible exclusively with a verified cryptographic JWT session token (`HS256`). Shows decoded payload and token expiry.
![Protected User Dashboard](screenshots/06_user_dashboard.png)

---

### 7. Dedicated Admin Control Center & Audit Directory
Displays real-time registered users directory and platform statistics. **Password data and hashes are strictly redacted.**
![Admin Dashboard](screenshots/07_admin_dashboard.png)

---

## ✅ Final Milestone 1 Checklist

| Step | Requirement | Status | Verification Detail |
|---|---|:---:|---|
| **Step 1** | Repository & `Milestone1` folder created | ✅ **PASS** | Sub-repository folder structure established |
| **Step 2** | Comprehensive `README.md` documented | ✅ **PASS** | Complete architecture, setup guide & screenshots |
| **Step 3** | Authentication Pages in Streamlit | ✅ **PASS** | Login, Signup, Forgot Password & Admin Portal |
| **Step 4** | ngrok Authentication Setup | ✅ **PASS** | Seamless `pyngrok` tunnel integration |
| **Step 5** | Gmail App Password for OTP | ✅ **PASS** | Automated Gmail SMTP delivery (STARTTLS:587) with Colab Secrets |
| **Step 6** | Google Colab Secrets Integration | ✅ **PASS** | `userdata.get` with zero hard-coded credentials |
| **Step 7** | JWT Session Management | ✅ **PASS** | `HS256` token issuance, expiry check & logout |
| **Step 8** | Mandatory, Email & Password Validation | ✅ **PASS** | `ab@cd.ef` rule, 8+ chars, uppercase, lowercase, digit, symbol |
| **Step 9** | Forgot Password Flow (Dual-Route) | ✅ **PASS** | Security Question route + Gmail OTP route |
| **Step 10**| Protected User Dashboard | ✅ **PASS** | Decoded JWT claims, expiry timer & logout |
| **Step 11**| Dedicated Admin Dashboard | ✅ **PASS** | Audit directory with password data strictly redacted |
| **Step 12**| Clean Notebook (`.ipynb`) & Screenshots | ✅ **PASS** | All outputs cleared, no hard-coded secrets, 7 screenshots |

---
**Author:** Infosys Springboard Intern  
**Program:** Infosys Springboard Internship 7.0 (Batch 4)  
**Milestone:** 1 (User Authentication Module)
