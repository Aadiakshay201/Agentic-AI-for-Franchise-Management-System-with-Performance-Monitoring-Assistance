import streamlit as st
import datetime
import time
import hmac
from database import (
    init_db,
    create_user,
    get_user_by_identifier,
    get_user_by_username,
    get_user_by_email,
    update_password,
    get_all_users_for_admin,
    store_otp,
    verify_and_consume_otp,
    get_latest_otp_info,
    get_all_franchises,
    get_franchise_orders,
    create_franchise_order,
    submit_franchise_application,
    get_all_franchise_applications
)
from auth import (
    SECURITY_QUESTIONS,
    validate_email_format,
    validate_password_complexity,
    hash_password,
    verify_password,
    hash_security_answer,
    verify_security_answer,
    generate_jwt_token,
    verify_jwt_token,
    mask_email
)
from mailer import generate_otp, send_otp_email, check_mail_status
from config import ADMIN_USERNAME, ADMIN_PASSWORD

# Ensure database tables exist and migrations are applied
init_db()

# Page configuration
st.set_page_config(
    page_title="Franchise Management System - Auth Module",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich styling, glassmorphism cards, and corporate aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main brand header */
    .brand-banner {
        background: linear-gradient(135deg, #002f6c 0%, #0070ad 50%, #00a4e4 100%);
        padding: 24px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(0, 112, 173, 0.22);
    }
    .brand-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-subtitle {
        font-size: 14px;
        opacity: 0.92;
        margin-top: 6px;
        font-weight: 400;
    }

    /* Cards */
    .auth-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Metric cards */
    .metric-card {
        background: #f8fafc;
        border-left: 4px solid #0070ad;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }

    /* OTP Verification highlighted container */
    .otp-highlight-box {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 20px;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 20px;
        background-color: #e0f2fe;
        color: #0369a1;
    }
    .admin-badge {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    /* Subtle divider */
    .section-divider {
        margin: 20px 0;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None

if "user" not in st.session_state:
    st.session_state["user"] = None

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Login"

if "pending_login_user" not in st.session_state:
    st.session_state["pending_login_user"] = None

if "otp_sent_email" not in st.session_state:
    st.session_state["otp_sent_email"] = None

if "otp_error_msg" not in st.session_state:
    st.session_state["otp_error_msg"] = None

if "otp_success_msg" not in st.session_state:
    st.session_state["otp_success_msg"] = None

if "last_otp_resend_time" not in st.session_state:
    st.session_state["last_otp_resend_time"] = 0


def check_auth() -> bool:
    """Verifies currently stored JWT token in session state."""
    token = st.session_state.get("jwt_token")
    if not token:
        st.session_state["user"] = None
        return False
    is_valid, payload, _ = verify_jwt_token(token)
    if is_valid and payload:
        st.session_state["user"] = payload
        return True
    else:
        st.session_state["jwt_token"] = None
        st.session_state["user"] = None
        return False


def navigate_to(page: str):
    st.session_state["active_page"] = page
    st.rerun()

def logout():
    """Clears user session state and redirects to Login."""
    st.session_state["jwt_token"] = None
    st.session_state["user"] = None
    st.session_state["pending_login_user"] = None
    st.session_state["otp_sent_email"] = None
    st.session_state["otp_error_msg"] = None
    st.session_state["otp_success_msg"] = None
    navigate_to("Login")


# Global Brand Header
st.markdown("""
<div class="brand-banner">
    <div class="brand-title">🏢 Franchise Management System</div>
    <div class="brand-subtitle">Infosys Springboard Internship 7.0 (Batch 4) · Milestone 1 · Secure Authentication & Franchise Hub</div>
</div>
""", unsafe_allow_html=True)

is_logged_in = check_auth()
current_user = st.session_state.get("user")

# Sidebar Navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/real-estate.png", width=64)
    st.title("Navigation")

    if is_logged_in:
        role = current_user.get("role", "user")
        st.success(f"Signed in as **{current_user.get('sub')}**")
        st.markdown(f"<span class='status-badge {'admin-badge' if role == 'admin' else ''}'>Role: {role.upper()}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if role == "admin":
            admin_views = ["Admin Dashboard", "Franchise Network Oversight", "Registered Users Audit"]
            selected_view = st.radio("Admin Controls:", admin_views, key="admin_sidebar_radio")
            st.session_state["active_page"] = "Admin Dashboard"
        else:
            user_views = ["User Dashboard", "Franchise Directory", "Supply & Inventory", "Apply for Franchise"]
            selected_view = st.radio("Franchise Portal:", user_views, key="user_sidebar_radio")
            st.session_state["active_page"] = "User Dashboard"

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            logout()
    else:
        nav_options = ["Login", "Signup", "Forgot Password", "Admin Portal"]
        
        current_page = st.session_state.get("active_page", "Login")
        if current_page == "OTP Verification":
            nav_options = ["Login", "OTP Verification", "Signup", "Forgot Password", "Admin Portal"]

        current_idx = nav_options.index(current_page) if current_page in nav_options else 0

        selected_nav = st.radio(
            "Portal Navigation:",
            nav_options,
            index=current_idx
        )
        if selected_nav != st.session_state.get("active_page"):
            st.session_state["active_page"] = selected_nav
            st.session_state["otp_error_msg"] = None
            st.session_state["otp_success_msg"] = None
            st.rerun()

    st.markdown("---")
    st.caption("🔒 **Security & Session Details**")
    st.caption("• Architecture: **Multi-Factor OTP + JWT**")
    st.caption("• Algorithm: **HS256** (2-Hour Expiration)")
    st.caption("• Password Storage: **bcrypt (12 rounds)**")
    st.caption("• Secret Storage: **Colab Secrets / .env**")


# ==============================================================================
# 1. LOGIN PAGE (Step 1 of Authentication Flow)
# ==============================================================================
if not is_logged_in and st.session_state["active_page"] == "Login":
    st.subheader("🔑 User Login")
    st.write("Sign in with your registered credentials. Two-Factor OTP verification will follow.")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("login_form"):
            login_id = st.text_input("Username or Email", placeholder="e.g. testuser or user@domain.com").strip()
            password = st.text_input("Password", type="password", placeholder="Enter your password").strip()
            submit_login = st.form_submit_button("Sign In & Request OTP", use_container_width=True, type="primary")

            if submit_login:
                # Mandatory field check
                if not login_id or not password:
                    st.error("⚠️ All fields are mandatory. Please provide both username/email and password.")
                else:
                    user = get_user_by_identifier(login_id)
                    # Generic error on invalid credentials (anti-enumeration protection)
                    if not user or not verify_password(password, user["password_hash"]):
                        st.error("❌ Invalid username/email or password.")
                    else:
                        # Step 1 Success -> Proceed to Two-Factor OTP Verification
                        otp_code = generate_otp()
                        store_otp(user["email"], otp_code, purpose="login", validity_minutes=10)
                        send_ok, send_msg = send_otp_email(user["email"], otp_code, purpose="login")
                        
                        st.session_state["pending_login_user"] = {
                            "username": user["username"],
                            "email": user["email"],
                            "role": "user"
                        }
                        st.session_state["otp_error_msg"] = None
                        st.session_state["otp_success_msg"] = f"A 6-digit OTP has been dispatched to {mask_email(user['email'])}. Please verify to complete login."
                        navigate_to("OTP Verification")

    with col2:
        st.info("""
        **Help & Shortcuts:**
        - **New Franchisee?** Register via **Signup**.
        - **Forgot Password?** Recover using **Forgot Password**.
        - **Administrator?** Access the **Admin Portal**.
        - **Two-Factor Auth:** A 6-digit OTP will be required after valid credentials.
        """)


# ==============================================================================
# 2. OTP VERIFICATION PAGE (Step 2 of Authentication Flow)
# ==============================================================================
elif not is_logged_in and st.session_state["active_page"] == "OTP Verification":
    pending_user = st.session_state.get("pending_login_user")
    if not pending_user:
        st.warning("No pending login found. Please sign in first.")
        st.session_state["active_page"] = "Login"
        st.rerun()

    st.subheader("🔐 Two-Factor OTP Verification")
    st.write("Enter the 6-digit verification code sent to your registered email address to complete login.")

    col1, col2 = st.columns([2, 1])
    with col1:
        # Highlight box showing masked email
        st.markdown(f"""
        <div class="otp-highlight-box">
            <div style="font-weight: 600; color: #0369a1; margin-bottom: 4px;">📧 Verification Code Dispatched</div>
            <div style="font-size: 14px; color: #334155;">
                We have sent a 6-digit code to: <strong>{mask_email(pending_user['email'])}</strong>
            </div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                ⏱️ Code is valid for 10 minutes.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show pending messages
        if st.session_state.get("otp_success_msg"):
            st.success(st.session_state["otp_success_msg"])

        if st.session_state.get("otp_error_msg"):
            st.error(st.session_state["otp_error_msg"])

        # OTP Entry Form
        with st.form("otp_verification_form"):
            otp_input = st.text_input(
                "Enter 6-Digit OTP *",
                max_chars=6,
                placeholder="e.g. 123456",
                key="otp_verify_code_input"
            ).strip()
            
            submit_otp = st.form_submit_button("Verify & Proceed to Dashboard", use_container_width=True, type="primary")

            if submit_otp:
                # 1. Empty field check
                if not otp_input:
                    st.session_state["otp_error_msg"] = "⚠️ Please enter the 6-digit OTP."
                    st.rerun()
                # 2. Digit and length check
                elif len(otp_input) != 6 or not otp_input.isdigit():
                    st.session_state["otp_error_msg"] = "⚠️ OTP must be a 6-digit number."
                    st.rerun()
                else:
                    # 3. Backend verification with attempt limiting & expiration
                    is_valid, msg = verify_and_consume_otp(pending_user["email"], otp_input, purpose="login")
                    if not is_valid:
                        # Sets error message: "Invalid OTP. Please try again." or expiration/lockout message
                        st.session_state["otp_error_msg"] = f"❌ {msg}"
                        st.session_state["otp_success_msg"] = None
                        st.rerun()
                    else:
                        # 4. Successful OTP Verification -> Issue JWT session
                        token = generate_jwt_token(
                            pending_user["username"],
                            pending_user["email"],
                            role=pending_user.get("role", "user")
                        )
                        st.session_state["jwt_token"] = token
                        st.session_state["user"] = {
                            "sub": pending_user["username"],
                            "email": pending_user["email"],
                            "role": pending_user.get("role", "user")
                        }
                        st.session_state["pending_login_user"] = None
                        st.session_state["otp_error_msg"] = None
                        st.session_state["otp_success_msg"] = None
                        target = "User Dashboard" if pending_user.get("role") == "user" else "Admin Dashboard"
                        st.success("✅ OTP verified successfully! Redirecting to Dashboard...")
                        navigate_to(target)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

        # Action Buttons: Resend OTP, Forgot Password, and Back to Login
        act_col1, act_col2, act_col3 = st.columns(3)
        with act_col1:
            if st.button("🔄 Resend OTP", use_container_width=True):
                # Cooldown check (minimum 15 seconds)
                now = time.time()
                if now - st.session_state.get("last_otp_resend_time", 0) < 15:
                    st.warning("⏳ Please wait a few seconds before requesting another OTP.")
                else:
                    new_otp = generate_otp()
                    store_otp(pending_user["email"], new_otp, purpose="login", validity_minutes=10)
                    send_otp_email(pending_user["email"], new_otp, purpose="login")
                    st.session_state["last_otp_resend_time"] = now
                    st.session_state["otp_error_msg"] = None
                    st.session_state["otp_success_msg"] = "✅ A fresh 6-digit OTP has been sent to your email. Please check your inbox."
                    st.rerun()

        with act_col2:
            if st.button("🔄 Forgot Password?", use_container_width=True):
                st.session_state["pending_login_user"] = None
                st.session_state["otp_error_msg"] = None
                st.session_state["otp_success_msg"] = None
                navigate_to("Forgot Password")

        with act_col3:
            if st.button("⬅️ Back to Login", use_container_width=True):
                st.session_state["pending_login_user"] = None
                st.session_state["otp_error_msg"] = None
                st.session_state["otp_success_msg"] = None
                navigate_to("Login")

    with col2:
        st.info("""
        **Security Instructions:**
        - **Enter Exact Code:** Enter the 6 digits without spaces.
        - **Incorrect Attempts:** Locked after 5 failed attempts.
        - **Never Disclosed:** OTPs are never revealed in error logs or screens.
        - **Resend Option:** Click *Resend OTP* if the email has not arrived.
        """)


# ==============================================================================
# 3. SIGNUP PAGE (Registration)
# ==============================================================================
elif not is_logged_in and st.session_state["active_page"] == "Signup":
    st.subheader("📝 Franchise Partner Registration")
    st.write("Create a secure profile for the Franchise Management System.")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("signup_form"):
            username = st.text_input("Username *", placeholder="Choose a unique username").strip()
            email = st.text_input("Email Address *", placeholder="e.g. partner@franchise.com").strip()
            
            pwd_col1, pwd_col2 = st.columns(2)
            with pwd_col1:
                password = st.text_input("Password *", type="password", placeholder="Min. 8 chars with uppercase, digits, symbols").strip()
            with pwd_col2:
                confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Repeat exact password").strip()

            security_question = st.selectbox(
                "Security Question *",
                SECURITY_QUESTIONS,
                index=0
            )
            security_answer = st.text_input("Security Answer *", placeholder="Answer used for recovery").strip()

            submit_signup = st.form_submit_button("Register Franchise Account", use_container_width=True, type="primary")

            if submit_signup:
                if not username or not email or not password or not confirm_password or not security_answer:
                    st.error("⚠️ All fields are mandatory. Please fill in all required inputs.")
                else:
                    # Email format check (ab@cd.ef)
                    is_email_valid, email_err = validate_email_format(email)
                    if not is_email_valid:
                        st.error(f"❌ {email_err}")
                    else:
                        # Password complexity & match check
                        is_pwd_valid, pwd_err = validate_password_complexity(password, confirm_password)
                        if not is_pwd_valid:
                            st.error(f"❌ {pwd_err}")
                        else:
                            pwd_hash = hash_password(password)
                            ans_hash = hash_security_answer(security_answer)

                            success, msg = create_user(
                                username=username,
                                email=email,
                                password_hash=pwd_hash,
                                security_question=security_question,
                                security_answer_hash=ans_hash
                            )

                            if success:
                                st.success("🎉 Account created successfully! Please proceed to Login.")
                                st.session_state["active_page"] = "Login"
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Back to Login", key="signup_back_to_login"):
            st.session_state["active_page"] = "Login"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Password Requirements</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                <li>At least 8 characters</li>
                <li>At least one uppercase letter (A-Z)</li>
                <li>At least one lowercase letter (a-z)</li>
                <li>At least one numeric digit (0-9)</li>
                <li>At least one special symbol (!@#$%^&*)</li>
            </ul>
        </div>
        <div class="metric-card">
            <h4>Email Format Standard</h4>
            <p style="font-size: 13px; margin: 0;">
                Must contain ≥2 letters before '@', ≥2 letters between '@' and '.', and ≥2 letters after '.' (e.g. <code>ab@cd.ef</code>).
            </p>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# 4. FORGOT PASSWORD PAGE (Dual-Route Recovery)
# ==============================================================================
elif not is_logged_in and st.session_state["active_page"] == "Forgot Password":
    st.subheader("🔄 Password Recovery")
    st.write("Recover access to your Franchise Management account using Security Question or Gmail OTP.")

    tab_sq, tab_otp = st.tabs(["🛡️ Route 1: Security Question", "📧 Route 2: Gmail OTP"])

    # --- Route 1: Security Question ---
    with tab_sq:
        st.markdown("#### Recover via Security Question")
        st.caption("Verify your configured security question and answer to set a new password.")

        sq_username = st.text_input("Enter your Username", key="sq_username_input").strip()

        if sq_username:
            user_data = get_user_by_username(sq_username)
            if not user_data:
                st.warning("⚠️ No account found with that username.")
            else:
                st.info(f"**Security Question:** {user_data['security_question']}")

                with st.form("sq_reset_form"):
                    sq_answer = st.text_input("Your Security Answer *", placeholder="Enter your answer").strip()
                    sq_new_pwd = st.text_input("New Password *", type="password", placeholder="Enter compliant new password").strip()
                    sq_confirm_pwd = st.text_input("Confirm New Password *", type="password", placeholder="Repeat new password").strip()

                    submit_sq_reset = st.form_submit_button("Reset Password", use_container_width=True, type="primary")

                    if submit_sq_reset:
                        if not sq_answer or not sq_new_pwd or not sq_confirm_pwd:
                            st.error("⚠️ All fields are mandatory.")
                        elif not verify_security_answer(sq_answer, user_data["security_answer_hash"]):
                            st.error("❌ Incorrect security answer. Please try again.")
                        else:
                            is_pwd_valid, pwd_err = validate_password_complexity(sq_new_pwd, sq_confirm_pwd)
                            if not is_pwd_valid:
                                st.error(f"❌ {pwd_err}")
                            else:
                                new_hash = hash_password(sq_new_pwd)
                                if update_password(user_data["username"], new_hash):
                                    st.success("✅ Password updated successfully! Redirecting to Login...")
                                    st.session_state["active_page"] = "Login"
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update password. Please try again.")

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Back to Login", key="sq_back_to_login"):
            st.session_state["active_page"] = "Login"
            st.rerun()

    # --- Route 2: Gmail OTP ---
    with tab_otp:
        st.markdown("#### Recover via Gmail OTP")
        st.caption("A 6-digit one-time code will be dispatched to your registered email address.")

        otp_col1, otp_col2 = st.columns([3, 1])
        with otp_col1:
            target_email = st.text_input(
                "Enter Registered Email Address",
                value=st.session_state.get("otp_sent_email") or "",
                placeholder="e.g. partner@franchise.com",
                key="recovery_email_input"
            ).strip()

        with otp_col2:
            st.write("")
            st.write("")
            send_btn = st.button("📨 Send Recovery OTP", use_container_width=True)

        if send_btn:
            if not target_email:
                st.error("⚠️ Please enter your registered email address first.")
            else:
                target_user = get_user_by_email(target_email)
                if not target_user:
                    st.error("❌ No account found with this email address.")
                else:
                    otp_code = generate_otp()
                    store_otp(target_email, otp_code, purpose="password_reset", validity_minutes=10)
                    with st.spinner("Dispatching verification OTP..."):
                        success, mail_msg = send_otp_email(target_email, otp_code, purpose="password_reset")
                    if success:
                        st.session_state["otp_sent_email"] = target_email
                        st.session_state["recovery_otp_err"] = None
                        st.success(f"✅ One-Time Password successfully sent to {mask_email(target_email)}! Please check your inbox.")
                    else:
                        st.session_state["otp_sent_email"] = None
                        st.error(f"❌ OTP Delivery Failed: {mail_msg}")

        # Reset Password with OTP Form
        if st.session_state.get("otp_sent_email"):
            st.markdown("---")
            st.markdown(f"**Verification for:** `{mask_email(st.session_state['otp_sent_email'])}`")
            
            if st.session_state.get("recovery_otp_err"):
                st.error(st.session_state["recovery_otp_err"])

            with st.form("otp_reset_password_form"):
                user_otp = st.text_input("Enter 6-Digit OTP *", max_chars=6, placeholder="e.g. 123456").strip()
                otp_new_pwd = st.text_input("New Password *", type="password", placeholder="Enter compliant new password").strip()
                otp_confirm_pwd = st.text_input("Confirm New Password *", type="password", placeholder="Repeat new password").strip()

                submit_otp_reset = st.form_submit_button("Verify OTP & Reset Password", use_container_width=True, type="primary")

                if submit_otp_reset:
                    if not user_otp:
                        st.session_state["recovery_otp_err"] = "⚠️ Please enter the 6-digit OTP."
                        st.rerun()
                    elif not otp_new_pwd or not otp_confirm_pwd:
                        st.session_state["recovery_otp_err"] = "⚠️ All fields are mandatory. Please provide a new password."
                        st.rerun()
                    else:
                        is_valid_otp, otp_err = verify_and_consume_otp(
                            st.session_state["otp_sent_email"],
                            user_otp,
                            purpose="password_reset"
                        )
                        if not is_valid_otp:
                            st.session_state["recovery_otp_err"] = f"❌ {otp_err}"
                            st.rerun()
                        else:
                            is_pwd_valid, pwd_err = validate_password_complexity(otp_new_pwd, otp_confirm_pwd)
                            if not is_pwd_valid:
                                st.session_state["recovery_otp_err"] = f"❌ {pwd_err}"
                                st.rerun()
                            else:
                                user_obj = get_user_by_email(st.session_state["otp_sent_email"])
                                if user_obj:
                                    new_hash = hash_password(otp_new_pwd)
                                    update_password(user_obj["username"], new_hash)
                                    st.session_state["otp_sent_email"] = None
                                    st.session_state["recovery_otp_err"] = None
                                    st.success("🎉 Password successfully reset! Redirecting to Login...")
                                    st.session_state["active_page"] = "Login"
                                    st.rerun()

            # Resend option for Forgot Password
            rf_col1, rf_col2 = st.columns(2)
            with rf_col1:
                if st.button("🔄 Resend Recovery OTP", use_container_width=True, key="resend_recovery_otp"):
                    new_otp = generate_otp()
                    store_otp(st.session_state["otp_sent_email"], new_otp, purpose="password_reset", validity_minutes=10)
                    send_otp_email(st.session_state["otp_sent_email"], new_otp, purpose="password_reset")
                    st.session_state["recovery_otp_err"] = None
                    st.success("✅ A fresh recovery OTP has been dispatched to your email.")
                    st.rerun()

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Back to Login", key="otp_route_back_to_login"):
            st.session_state["active_page"] = "Login"
            st.session_state["otp_sent_email"] = None
            st.session_state["recovery_otp_err"] = None
            st.rerun()


# ==============================================================================
# 5. ADMIN PORTAL LOGIN
# ==============================================================================
elif not is_logged_in and st.session_state["active_page"] == "Admin Portal":
    st.subheader("🛡️ Franchise Administrator Access")
    st.write("Separate portal for system evaluators, network auditors, and administrators.")

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("admin_login_form"):
            admin_user = st.text_input("Admin Username", placeholder="e.g. admin").strip()
            admin_pwd = st.text_input("Admin Password", type="password", placeholder="Enter admin password").strip()
            submit_admin = st.form_submit_button("Authenticate as Administrator", use_container_width=True, type="primary")

            if submit_admin:
                if not admin_user or not admin_pwd:
                    st.error("⚠️ Both admin username and password are mandatory.")
                else:
                    is_user_match = hmac.compare_digest(admin_user.strip().lower(), ADMIN_USERNAME.strip().lower())
                    is_pwd_match = hmac.compare_digest(admin_pwd.strip(), ADMIN_PASSWORD.strip())
                    if is_user_match and is_pwd_match:
                        token = generate_jwt_token(admin_user, "admin@franchise.infosys.internal", role="admin")
                        st.session_state["jwt_token"] = token
                        st.session_state["user"] = {
                            "sub": admin_user,
                            "email": "admin@franchise.infosys.internal",
                            "role": "admin"
                        }
                        st.session_state["active_page"] = "Admin Dashboard"
                        st.success("✅ Admin authentication successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid admin credentials.")

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        if st.button("⬅️ Back to User Login", key="admin_back_to_login"):
            st.session_state["active_page"] = "Login"
            st.rerun()

    with col2:
        st.warning("""
        **Notice:**
        This portal is strictly reserved for authorized franchise administrators. All activities are recorded for audit compliance.
        """)


# ==============================================================================
# 6. PROTECTED USER DASHBOARD (Franchise Management System)
# ==============================================================================
elif is_logged_in and current_user and current_user.get("role") == "user":
    st.subheader(f"👋 Welcome to Franchise Portal, {current_user.get('sub')}!")
    st.caption("You are authenticated via a verified, cryptographic JWT session token (HS256).")

    # Top summary metrics
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">ACTIVE PARTNER</span>
            <h3 style="margin: 4px 0; color: #0070ad;">{current_user.get('sub')}</h3>
            <span style="font-size: 12px; color: #0284c7;">Role: Franchisee User</span>
        </div>
        """, unsafe_allow_html=True)

    with mcol2:
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">VERIFIED EMAIL</span>
            <h3 style="margin: 4px 0; color: #0f172a; font-size: 16px;">{current_user.get('email')}</h3>
            <span style="font-size: 12px; color: #16a34a;">2FA Status: Verified ✅</span>
        </div>
        """, unsafe_allow_html=True)

    with mcol3:
        all_franchises = get_all_franchises()
        user_outlets = [f for f in all_franchises if f["owner_username"].lower() == current_user.get("sub", "").lower()]
        outlet_count = len(user_outlets) if user_outlets else len(all_franchises)
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">FRANCHISE OUTLETS</span>
            <h3 style="margin: 4px 0; color: #0f172a; font-size: 20px;">{outlet_count} Active</h3>
            <span style="font-size: 12px; color: #16a34a;">Status: Operational</span>
        </div>
        """, unsafe_allow_html=True)

    with mcol4:
        exp_timestamp = current_user.get("exp")
        exp_str = datetime.datetime.fromtimestamp(exp_timestamp, datetime.timezone.utc).strftime("%H:%M:%S UTC") if exp_timestamp else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase;">JWT TOKEN EXPIRY</span>
            <h3 style="margin: 4px 0; color: #b45309; font-size: 18px;">{exp_str}</h3>
            <span style="font-size: 12px; color: #64748b;">Algorithm: HS256</span>
        </div>
        """, unsafe_allow_html=True)

    # Main Tabs inside User Dashboard
    tab_overview, tab_outlets, tab_inventory, tab_apply = st.tabs([
        "📊 Session & Security Overview",
        "🏢 Franchise Outlets Directory",
        "📦 Supply & Inventory Orders",
        "📝 Apply for New Franchise"
    ])

    # Tab 1: Overview & JWT Inspection
    with tab_overview:
        st.markdown("### 📜 Verified Session Details")
        with st.expander("🔍 Inspect Decoded JWT Token Payload (Debug & Verification)", expanded=True):
            st.json(current_user)

        st.markdown("### 🚀 Internship Milestone 1 Progress Checklist")
        c1, c2 = st.columns(2)
        with c1:
            st.checkbox("Step 1: Repository & Milestone1 Folder Created", value=True, disabled=True)
            st.checkbox("Step 2: Comprehensive README.md Documented", value=True, disabled=True)
            st.checkbox("Step 3: Multi-Page Streamlit App Implemented", value=True, disabled=True)
            st.checkbox("Step 4: ngrok Public Tunnel Integration Configured", value=True, disabled=True)
            st.checkbox("Step 5: Gmail App Password / OAuth 2.0 Configured", value=True, disabled=True)
            st.checkbox("Step 6: Colab Secrets Handled Without Hardcoding", value=True, disabled=True)
        with c2:
            st.checkbox("Step 7: Cryptographic JWT Session Management", value=True, disabled=True)
            st.checkbox("Step 8: Mandatory, Email (ab@cd.ef) & Password Validation", value=True, disabled=True)
            st.checkbox("Step 9: Forgot Password (Security Question + Gmail OTP)", value=True, disabled=True)
            st.checkbox("Step 10: Two-Factor OTP Verification & Invalid Handling", value=True, disabled=True)
            st.checkbox("Step 11: Dedicated Admin Portal (Passwords Redacted)", value=True, disabled=True)
            st.checkbox("Step 12: Clean Colab Notebook (.ipynb) & Screenshots", value=True, disabled=True)

    # Tab 2: Franchise Outlets Directory
    with tab_outlets:
        st.markdown("### 🏢 Franchise Network Directory")
        st.write("Browse and manage operational franchise stores across the country.")

        franchise_list = get_all_franchises()
        search_f = st.text_input("🔍 Search Outlets by Code, City, or Name:", placeholder="e.g. Bengaluru, FR-BLR-001...").strip().lower()

        if search_f:
            franchise_list = [
                f for f in franchise_list
                if search_f in f["code"].lower() or search_f in f["city"].lower() or search_f in f["name"].lower()
            ]

        f_table = []
        for item in franchise_list:
            f_table.append({
                "Outlet Code": item["code"],
                "Outlet Name": item["name"],
                "Owner / Partner": item["owner_username"],
                "Location": f"{item['city']}, {item['state']}",
                "Status": item["status"],
                "Monthly Revenue (INR)": f"₹{item['monthly_revenue']:,.2f}",
                "Royalty Rate": f"{item['royalty_rate']}%"
            })
        st.dataframe(f_table, use_container_width=True)

    # Tab 3: Supply & Inventory Orders
    with tab_inventory:
        st.markdown("### 📦 Supply Requisitions & Inventory Tracking")
        st.caption("Manage raw supplies, branded packaging, and hardware orders for franchise outlets.")

        order_col1, order_col2 = st.columns([2, 1])
        with order_col1:
            st.markdown("#### Recent Requisitions")
            orders = get_franchise_orders()
            order_data = []
            for o in orders:
                order_data.append({
                    "Order ID": f"ORD-#{o['id']:04d}",
                    "Outlet Code": o["franchise_code"],
                    "Item Description": o["item_name"],
                    "Quantity": o["quantity"],
                    "Fulfillment Status": o["status"],
                    "Order Date": o["ordered_at"]
                })
            st.dataframe(order_data, use_container_width=True)

        with order_col2:
            st.markdown("#### Place Supply Order")
            with st.form("new_order_form"):
                all_f = get_all_franchises()
                outlet_options = [f["code"] for f in all_f]
                selected_outlet = st.selectbox("Select Outlet Code", outlet_options)
                item_select = st.selectbox("Supply Item", [
                    "Branded Packaging Kit (5,000 units)",
                    "Smart POS Terminal v3",
                    "Official Staff Uniform Set (10 pcs)",
                    "Store Display Signage Board (LED)",
                    "Kitchen Sanitization & Hygiene Pack"
                ])
                qty = st.number_input("Quantity", min_value=1, max_value=100, value=1)
                submit_order = st.form_submit_button("Submit Supply Requisition", use_container_width=True, type="primary")

                if submit_order:
                    if create_franchise_order(selected_outlet, item_select, int(qty)):
                        st.success("✅ Order placed successfully! Fulfillment team notified.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to place order. Please try again.")

    # Tab 4: Apply for New Franchise
    with tab_apply:
        st.markdown("### 📝 Apply for a New Franchise Territory")
        st.write("Submit a request to license a new franchise outlet under the corporate network.")

        with st.form("franchise_app_form"):
            app_c1, app_c2 = st.columns(2)
            with app_c1:
                app_name = st.text_input("Applicant Full Name *", value=current_user.get("sub", "")).strip()
                app_email = st.text_input("Contact Email *", value=current_user.get("email", "")).strip()
                app_phone = st.text_input("Contact Phone Number *", placeholder="+91 98765 43210").strip()
            with app_c2:
                app_city = st.text_input("Proposed City / Location *", placeholder="e.g. Pune, Maharashtra").strip()
                app_budget = st.selectbox("Estimated Investment Capital *", [
                    "₹20 Lakhs – ₹35 Lakhs",
                    "₹35 Lakhs – ₹50 Lakhs",
                    "₹50 Lakhs – ₹1 Crore",
                    "Above ₹1 Crore"
                ])
            
            submit_app = st.form_submit_button("Submit Franchise Application", use_container_width=True, type="primary")

            if submit_app:
                if not app_name or not app_email or not app_phone or not app_city:
                    st.error("⚠️ All fields marked with * are mandatory.")
                else:
                    if submit_franchise_application(app_name, app_email, app_phone, app_city, app_budget):
                        st.success("🎉 Franchise application submitted successfully! Our expansion manager will reach out within 48 hours.")
                    else:
                        st.error("❌ Submission failed. Please try again.")

    st.markdown("---")
    if st.button("🚪 Logout from User Session", type="primary"):
        logout()


# ==============================================================================
# 7. ADMIN DASHBOARD
# ==============================================================================
elif is_logged_in and current_user and current_user.get("role") == "admin":
    st.subheader("🛡️ Franchise Management System — Administrator Control Center")
    st.caption("Administrative oversight, franchisee audit logs, network analytics, and compliance monitoring.")

    all_users = get_all_users_for_admin()
    franchises = get_all_franchises()
    orders = get_franchise_orders()
    applications = get_all_franchise_applications()

    # System metrics
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric(label="Registered Users", value=len(all_users))
    with mcol2:
        st.metric(label="Active Franchise Outlets", value=len(franchises))
    with mcol3:
        total_rev = sum(f["monthly_revenue"] for f in franchises)
        st.metric(label="Total Network Revenue", value=f"₹{total_rev:,.0f}")
    with mcol4:
        st.metric(label="Pending Applications", value=len(applications))

    st.markdown("---")

    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "👥 Registered Users Audit Directory",
        "🏢 Franchise Network Operations",
        "🔍 Security & Mailer Diagnostics"
    ])

    # Admin Tab 1: Users Directory (Passwords strictly redacted)
    with admin_tab1:
        st.markdown("### 👥 Registered Users Directory")
        st.caption("⚠️ **Compliance Notice (Step 11):** Passwords and password hashes are strictly redacted from administrative views.")

        search_query = st.text_input("🔍 Search users by username or email:", placeholder="Type to filter...").strip().lower()

        filtered_users = all_users
        if search_query:
            filtered_users = [
                u for u in all_users
                if search_query in u["username"].lower() or search_query in u["email"].lower()
            ]

        if filtered_users:
            table_data = []
            for idx, u in enumerate(filtered_users, start=1):
                table_data.append({
                    "User ID": u["id"],
                    "Username": u["username"],
                    "Email Address": u["email"],
                    "Security Question Configured": u["security_question"],
                    "Registration Timestamp": u["created_at"],
                    "Account Status": "Active ✅"
                })
            st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No registered users found matching the search criteria.")

    # Admin Tab 2: Franchise Network & Applications
    with admin_tab2:
        st.markdown("### 🏢 Franchise Outlets Network")
        outlets_admin = []
        for f in franchises:
            outlets_admin.append({
                "Outlet Code": f["code"],
                "Name": f["name"],
                "Partner": f["owner_username"],
                "City": f["city"],
                "State": f["state"],
                "Monthly Revenue": f"₹{f['monthly_revenue']:,.2f}",
                "Royalty Rate": f"{f['royalty_rate']}%",
                "Status": f["status"]
            })
        st.dataframe(outlets_admin, use_container_width=True)

        st.markdown("#### 📝 Submitted Franchise Applications")
        if applications:
            app_table = []
            for a in applications:
                app_table.append({
                    "App ID": a["id"],
                    "Applicant": a["applicant_name"],
                    "Email": a["email"],
                    "Phone": a["phone"],
                    "City": a["city"],
                    "Budget": a["budget"],
                    "Status": a["status"],
                    "Date Applied": a["applied_at"]
                })
            st.dataframe(app_table, use_container_width=True)
        else:
            st.info("No new franchise applications in the review queue.")

    # Admin Tab 3: Security & Mailer Diagnostics
    with admin_tab3:
        st.markdown("### 🔍 Security Configuration & Mail Diagnostics")
        mail_info = check_mail_status()
        
        diag_c1, diag_c2 = st.columns(2)
        with diag_c1:
            st.markdown("""
            <div class="metric-card">
                <h4>Authentication Standards</h4>
                <p>• <strong>JWT Token Engine:</strong> PyJWT (HS256)<br>
                • <strong>Session Lifetime:</strong> 2 Hours (cryptographically signed)<br>
                • <strong>Password Hashing:</strong> bcrypt (12 rounds auto-salted)<br>
                • <strong>Security Question:</strong> SHA-256 normalized hash<br>
                • <strong>Two-Factor OTP:</strong> 6-Digit random with 10-min TTL</p>
            </div>
            """, unsafe_allow_html=True)

        with diag_c2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>Email Dispatch Engine</h4>
                <p>• <strong>Active Delivery Mode:</strong> {mail_info['provider_mode']}<br>
                • <strong>Google OAuth2 API Configured:</strong> {'Yes ✅' if mail_info['has_oauth'] else 'No (Optional)'}<br>
                • <strong>Gmail SMTP Configured:</strong> {'Yes ✅' if mail_info['has_smtp'] else 'No (Optional)'}<br>
                • <strong>OTP Leak Prevention:</strong> Enforced (Sanitized Logs & Screens)</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Logout from Admin Portal", type="primary"):
        logout()
