import os
import shutil
import secrets
from pathlib import Path
from typing import Tuple, List, Dict
from dotenv import load_dotenv

# Search for and load local .env files from multiple possible locations
# (Milestone1 folder, repository root, current working directory, /content in Colab)
ENV_SEARCH_PATHS = [
    Path(__file__).resolve().parent / ".env",
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    Path("/content/.env")
]

for p in ENV_SEARCH_PATHS:
    if p.exists() and p.is_file():
        load_dotenv(p, override=False)

# Supported secret aliases covering uppercase, lowercase, and common variations
KEY_ALIASES: Dict[str, List[str]] = {
    "EMAIL_ADDRESS": [
        "email_address",
        "GMAIL_ADDRESS", "gmail_address",
        "EMAIL", "email",
        "GMAIL", "gmail",
        "EMAIL_USER", "email_user",
        "GMAIL_USER", "gmail_user",
        "GMAIL_EMAIL", "gmail_email",
        "SENDER_EMAIL", "sender_email",
        "SENDER_GMAIL", "sender_gmail",
        "USER_EMAIL", "user_email",
        "MAIL_USERNAME", "mail_username",
        "SMTP_USER", "smtp_user",
        "SMTP_EMAIL", "smtp_email",
        "GOOGLE_EMAIL", "google_email"
    ],
    "EMAIL_PASSWORD": [
        "email_password",
        "GMAIL_APP_PASSWORD", "gmail_app_password",
        "GMAIL_PASSWORD", "gmail_password",
        "EMAIL_APP_PASSWORD", "email_app_password",
        "APP_PASSWORD", "app_password",
        "GOOGLE_APP_PASSWORD", "google_app_password",
        "GMAIL_PASS", "gmail_pass",
        "EMAIL_PASS", "email_pass",
        "APP_PASS", "app_pass",
        "GMAIL_APP_PASS", "gmail_app_pass",
        "MAIL_PASSWORD", "mail_password",
        "SMTP_PASSWORD", "smtp_password",
        "SMTP_PASS", "smtp_pass"
    ],
    "JWT_SECRET": [
        "jwt_secret",
        "SECRET_KEY", "secret_key",
        "JWT_KEY", "jwt_key"
    ],
    "NGROK_AUTHTOKEN": [
        "ngrok_authtoken",
        "NGROK_AUTH_TOKEN", "ngrok_auth_token",
        "AUTHTOKEN", "authtoken"
    ],
    "ADMIN_USERNAME": [
        "admin_username"
    ],
    "ADMIN_PASSWORD": [
        "admin_password"
    ],
    "DB_PATH": [
        "db_path",
        "DATABASE_PATH", "database_path",
        "DATABASE_URL", "database_url"
    ],
    "GMAIL_CLIENT_ID": [
        "gmail_client_id", "CLIENT_ID", "client_id", "GOOGLE_CLIENT_ID", "google_client_id"
    ],
    "GMAIL_CLIENT_SECRET": [
        "gmail_client_secret", "CLIENT_SECRET", "client_secret", "GOOGLE_CLIENT_SECRET", "google_client_secret"
    ],
    "GMAIL_REFRESH_TOKEN": [
        "gmail_refresh_token", "REFRESH_TOKEN", "refresh_token", "GOOGLE_REFRESH_TOKEN", "google_refresh_token"
    ],
    "BREVO_API_KEY": [
        "brevo_api_key", "EMAIL_API_KEY", "email_api_key", "SENDINBLUE_API_KEY", "sendinblue_api_key", "BREVO_KEY", "brevo_key"
    ],
    "RESEND_API_KEY": [
        "resend_api_key", "RESEND_KEY", "resend_key"
    ]
}

# Diagnostic status dictionary without exposing secret values
_SECRET_STATUS: Dict[str, str] = {}

def sync_colab_secrets_to_env() -> None:
    """
    If running inside Google Colab, bridge Colab Secrets into os.environ
    and persistent .env files so background subprocesses (like Streamlit)
    can reliably access them.
    """
    try:
        from google.colab import userdata  # type: ignore
        from google.colab.userdata import NotebookAccessError, SecretNotFoundError  # type: ignore
    except ImportError:
        userdata = None
        NotebookAccessError = Exception
        SecretNotFoundError = Exception

    if not userdata:
        return

    env_updates = {}
    for primary_key, aliases in KEY_ALIASES.items():
        candidate_keys = [primary_key] + aliases
        val = None
        for k in candidate_keys:
            try:
                v = userdata.get(k)
                if v is not None and str(v).strip():
                    val = str(v).strip()
                    _SECRET_STATUS[primary_key] = f"Found in Colab Secrets via '{k}'"
                    break
            except NotebookAccessError:
                _SECRET_STATUS[primary_key] = (
                    f"Configured in Colab Secrets as '{k}', but 'Notebook access' toggle is OFF. "
                    "Please toggle 'Notebook access' ON in the Colab Secrets sidebar."
                )
            except SecretNotFoundError:
                continue
            except Exception:
                continue

        if val:
            os.environ[primary_key] = val
            env_updates[primary_key] = val

    # Persist secrets to .env in parent directory and /content if available
    if env_updates:
        target_files = [Path(__file__).resolve().parent / ".env"]
        if Path("/content").exists():
            target_files.append(Path("/content/.env"))

        for target in target_files:
            try:
                existing = {}
                if target.exists():
                    for line in target.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            existing[k.strip()] = v.strip()
                existing.update(env_updates)
                target.write_text(
                    "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n",
                    encoding="utf-8"
                )
            except Exception:
                pass

# Synchronize secrets if running in Colab notebook environment
sync_colab_secrets_to_env()

def get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves a configuration secret without exposing values.
    Prioritizes:
    1. OS environment variables (os.environ, including .env)
    2. Google Colab Secrets (userdata.get), supporting all candidate aliases
    3. Falls back to default.
    """
    candidate_keys = [key] + KEY_ALIASES.get(key, [])

    # 1. Check OS environment variables first (fast and subprocess-friendly)
    for k in candidate_keys:
        val = os.getenv(k)
        if val is not None and str(val).strip():
            val_str = str(val).strip()
            os.environ[key] = val_str
            return val_str

    # 2. Check Google Colab Secrets
    try:
        from google.colab import userdata  # type: ignore
        from google.colab.userdata import NotebookAccessError, SecretNotFoundError  # type: ignore
        for k in candidate_keys:
            try:
                val = userdata.get(k)
                if val is not None and str(val).strip():
                    val_str = str(val).strip()
                    os.environ[key] = val_str
                    _SECRET_STATUS[key] = f"Loaded from Colab Secrets via '{k}'"
                    return val_str
            except NotebookAccessError:
                _SECRET_STATUS[key] = (
                    f"Secret '{k}' found in Colab Secrets, but 'Notebook access' toggle is OFF. "
                    "Please toggle 'Notebook access' ON in Colab's Secrets tab."
                )
            except Exception:
                pass
    except Exception:
        pass

    return default

def get_secret_status(key: str) -> str:
    """Returns safe diagnostic info about why a secret was or wasn't loaded."""
    if key in _SECRET_STATUS:
        return _SECRET_STATUS[key]
    val = get_secret(key, "")
    if val:
        return "Configured and available"
    return "Not set in Colab Secrets or .env"

# Ephemeral fallback JWT Secret if none configured
_configured_jwt = get_secret("JWT_SECRET", "")
if not _configured_jwt:
    JWT_SECRET = secrets.token_hex(32)
else:
    JWT_SECRET = _configured_jwt

# ngrok Authtoken
NGROK_AUTHTOKEN = get_secret("NGROK_AUTHTOKEN", "")

# Gmail SMTP Configuration for OTP Delivery (evaluated dynamically when sending)
EMAIL_ADDRESS = get_secret("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = get_secret("EMAIL_PASSWORD", "")

# HTTPS Email Delivery Configurations (Gmail OAuth2 & Transactional APIs)
GMAIL_CLIENT_ID = get_secret("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = get_secret("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = get_secret("GMAIL_REFRESH_TOKEN", "")
BREVO_API_KEY = get_secret("BREVO_API_KEY", "") or get_secret("EMAIL_API_KEY", "")
RESEND_API_KEY = get_secret("RESEND_API_KEY", "")

# Dedicated Admin credentials
ADMIN_USERNAME = get_secret("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "Admin@Placeholder2026!")

def get_db_path() -> Path:
    """
    Resolves persistent SQLite database path across restarts and Colab disconnects.
    - If running in Colab and Google Drive is mounted (/content/drive/MyDrive),
      stores the database in: /content/drive/MyDrive/Infosys_Springboard_Milestone1/auth_system.db
      to guarantee persistence across Colab runtime recycles.
      If persistent DB does not exist yet but local DB exists, automatically copies
      the local database so existing records are preserved.
    - Otherwise (local development), stores the database in the local project directory:
      Milestone1/auth_system.db.
    - Preserves existing records; never deletes or resets the database.
    """
    custom = os.getenv("DB_PATH")
    if custom:
        p = Path(custom).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    local_path = Path(__file__).resolve().parent / "auth_system.db"

    # Google Colab persistent Google Drive storage check
    drive_mount = Path("/content/drive/MyDrive")
    if drive_mount.exists():
        persistent_dir = drive_mount / "Infosys_Springboard_Milestone1"
        try:
            persistent_dir.mkdir(parents=True, exist_ok=True)
            persistent_db = persistent_dir / "auth_system.db"

            # Seed persistent DB from local DB if local DB exists and persistent DB doesn't yet
            if not persistent_db.exists() and local_path.exists():
                try:
                    shutil.copy2(local_path, persistent_db)
                except Exception:
                    pass

            return persistent_db
        except Exception:
            return local_path

    return local_path

# Database path (initialized to resolved path)
DB_PATH = get_db_path()
