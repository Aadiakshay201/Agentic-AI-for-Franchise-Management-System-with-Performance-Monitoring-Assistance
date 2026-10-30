import re
import datetime
from typing import Tuple, Optional, Dict, Any
import jwt
import bcrypt
import hashlib
from config import JWT_SECRET

# Fixed list of security questions for Signup and Recovery
SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What was the name of your elementary school?",
    "In what city or town was your first job?",
    "What is your mother's maiden name?",
    "What was the make and model of your first car?",
    "What is your favorite childhood book or movie?"
]

def validate_email_format(email: str) -> Tuple[bool, str]:
    """
    Validates email according to Milestone 1 Step 8:
    'At least 2 letters before the @, at least 2 letters between the @ and the dot,
    and at least 2 letters after the final dot — e.g. an address shaped like ab@cd.ef.'
    """
    if not email:
        return False, "Email address is required."

    email = email.strip()
    if "@" not in email:
        return False, "Invalid email format: missing '@'."

    parts = email.split("@")
    if len(parts) != 2:
        return False, "Invalid email format: must contain exactly one '@'."

    local_part, domain_part = parts[0], parts[1]

    # At least 2 characters before the @
    if len(local_part) < 2:
        return False, "Email must have at least 2 characters before the '@' symbol (e.g. ab@cd.ef)."

    # Domain part checks
    if "." not in domain_part:
        return False, "Email domain must contain a dot '.'."

    domain_segments = domain_part.split(".")
    # Check segment between @ and dot, and all intermediate segments
    for seg in domain_segments[:-1]:
        if len(seg) < 2:
            return False, f"Domain section '{seg}' must contain at least 2 characters (e.g. ab@cd.ef)."

    # Final top-level domain (after final dot)
    tld = domain_segments[-1]
    if len(tld) < 2:
        return False, "Domain suffix after the final dot must contain at least 2 characters (e.g. .com, .ef)."

    # Regex safety check
    pattern = r"^[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9.-]{2,}\.[A-Za-z]{2,}$"
    if not re.match(pattern, email):
        return False, "Email contains unsupported characters. Please use a standard email address format."

    return True, ""

def validate_password_complexity(password: str, confirm_password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates password complexity according to Milestone 1 Step 8:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special symbol
    - Confirm Password must exactly match Password
    """
    if not password:
        return False, "Password cannot be empty."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one numeric digit (0-9)."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+[\]\\/`~;']", password):
        return False, "Password must contain at least one special symbol (!@#$%^&* etc.)."

    if confirm_password is not None:
        if password != confirm_password:
            return False, "Passwords do not match. Please verify Confirm Password."

    return True, ""

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def hash_security_answer(answer: str) -> str:
    """Normalizes and hashes security answer with SHA-256 for privacy."""
    normalized = answer.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def verify_security_answer(user_input: str, stored_hash: str) -> bool:
    """Checks if the user's answer matches the stored hash."""
    return hash_security_answer(user_input) == stored_hash

def generate_jwt_token(username: str, email: str, role: str = "user", hours_valid: int = 2) -> str:
    """
    Generates a signed JWT session token with expiration.
    Payload includes username, email, role, issued at, and expiration.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=hours_valid)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Decodes and validates a JWT session token.
    Returns: (is_valid, payload_dict, message)
    """
    if not token:
        return False, None, "No session token provided."

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return True, payload, "Token is active and valid."
    except jwt.ExpiredSignatureError:
        return False, None, "Your session has expired. Please log in again."
    except jwt.InvalidTokenError:
        return False, None, "Invalid session token. Please log in again."
    except Exception as e:
        return False, None, f"Authentication error: {str(e)}"

def mask_email(email: str) -> str:
    """Masks an email for safe display, e.g., j***e@domain.com."""
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@", 1)
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
    return f"{masked_user}@{domain}"
