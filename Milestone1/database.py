import sqlite3
import time
from typing import Optional, List, Dict, Tuple
from config import DB_PATH, get_db_path

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row access to persistent DB."""
    resolved_path = get_db_path()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes tables for users, OTP verification, and franchise management."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                security_question TEXT NOT NULL,
                security_answer_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # OTP verification table with attempts and purpose tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at REAL NOT NULL,
                used INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                purpose TEXT DEFAULT 'login',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Backward compatibility migration for older DB schemas
        try:
            cursor.execute("ALTER TABLE otps ADD COLUMN attempts INTEGER DEFAULT 0")
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE otps ADD COLUMN purpose TEXT DEFAULT 'login'")
        except Exception:
            pass

        # Franchise Outlets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS franchises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                owner_username TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                status TEXT DEFAULT 'Active',
                monthly_revenue REAL DEFAULT 0.0,
                royalty_rate REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Franchise Supply Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS franchise_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                franchise_code TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT DEFAULT 'Processing',
                ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Franchise Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS franchise_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                city TEXT NOT NULL,
                budget TEXT NOT NULL,
                status TEXT DEFAULT 'Under Review',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed initial sample franchise data if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM franchises")
        if cursor.fetchone()["cnt"] == 0:
            seed_franchises = [
                ("FR-BLR-001", "Infosys Hub Bengaluru", "testuser", "Bengaluru", "Karnataka", "Active", 1250000.0, 5.0),
                ("FR-MUM-002", "Marine Drive Express", "testuser", "Mumbai", "Maharashtra", "Active", 1850000.0, 5.5),
                ("FR-DEL-003", "Connaught Place Central", "aadiakshay", "New Delhi", "Delhi NCR", "Active", 1420000.0, 5.0),
                ("FR-HYD-004", "HITEC City Bistro", "aadiakshay", "Hyderabad", "Telangana", "Active", 1100000.0, 4.5),
                ("FR-CHN-005", "Marina Beach Bay Outlet", "testuser", "Chennai", "Tamil Nadu", "Under Audit", 890000.0, 5.0),
            ]
            cursor.executemany("""
                INSERT INTO franchises (code, name, owner_username, city, state, status, monthly_revenue, royalty_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, seed_franchises)

        # Seed initial orders if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM franchise_orders")
        if cursor.fetchone()["cnt"] == 0:
            seed_orders = [
                ("FR-BLR-001", "Branded Packaging Kit (5,000 units)", 2, "Delivered"),
                ("FR-BLR-001", "Smart POS Terminal v3", 3, "In Transit"),
                ("FR-MUM-002", "Official Staff Uniform Set (Medium)", 15, "Delivered"),
                ("FR-DEL-003", "Store Display Signage Board (LED)", 1, "Processing"),
                ("FR-HYD-004", "Kitchen Equipment Maintenance Pack", 1, "Delivered"),
            ]
            cursor.executemany("""
                INSERT INTO franchise_orders (franchise_code, item_name, quantity, status)
                VALUES (?, ?, ?, ?)
            """, seed_orders)

        conn.commit()

def create_user(
    username: str,
    email: str,
    password_hash: str,
    security_question: str,
    security_answer_hash: str
) -> Tuple[bool, str]:
    """
    Registers a new user.
    Ensures username and email uniqueness.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Check username collision
            cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
            if cursor.fetchone():
                return False, "Username is already taken. Please choose another username."

            # Check email collision
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            if cursor.fetchone():
                return False, "An account with this email already exists."

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username.strip(), email.strip().lower(), password_hash, security_question, security_answer_hash)
            )
            conn.commit()
            return True, "User registered successfully!"
    except sqlite3.IntegrityError as e:
        return False, f"Registration failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during registration: {str(e)}"

def get_user_by_username(username: str) -> Optional[Dict]:
    """Finds user by exact or case-insensitive username."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Finds user by case-insensitive email."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_identifier(identifier: str) -> Optional[Dict]:
    """Finds user by either username or email."""
    clean = identifier.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
            (clean, clean)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def update_password(username: str, new_password_hash: str) -> bool:
    """Updates password hash for a given user."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE LOWER(username) = LOWER(?)",
                (new_password_hash, username.strip())
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception:
        return False

def get_all_users_for_admin() -> List[Dict]:
    """
    Retrieves all registered users for Admin Dashboard.
    CRITICAL: Never fetches password_hash or security_answer_hash (Step 11 requirement).
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, security_question, created_at FROM users ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# ==============================================================================
# OTP OPERATIONS (Robust handling, attempt limits & expiration)
# ==============================================================================

MAX_OTP_ATTEMPTS = 5

def store_otp(email: str, otp_code: str, purpose: str = "login", validity_minutes: int = 10) -> bool:
    """
    Stores a generated OTP with expiration timestamp, purpose, and 0 initial attempts.
    Invalidates any previous unused OTP for this email with the same purpose.
    """
    try:
        expires_at = time.time() + (validity_minutes * 60)
        with get_connection() as conn:
            cursor = conn.cursor()
            # Invalidate older unused OTPs for this email and purpose
            cursor.execute(
                "UPDATE otps SET used = 1 WHERE LOWER(email) = LOWER(?) AND purpose = ? AND used = 0",
                (email.strip(), purpose)
            )
            cursor.execute(
                """
                INSERT INTO otps (email, otp_code, expires_at, used, attempts, purpose)
                VALUES (?, ?, ?, 0, 0, ?)
                """,
                (email.strip().lower(), otp_code.strip(), expires_at, purpose)
            )
            conn.commit()
            return True
    except Exception:
        return False

def verify_and_consume_otp(email: str, otp_code: str, purpose: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verifies the provided OTP against the active unexpired OTPs in the database.
    Enforces:
    - Non-empty check
    - Used status check
    - Expiration check
    - Max attempts limit (locks after MAX_OTP_ATTEMPTS incorrect entries)
    - Exact error message on mismatch: 'Invalid OTP. Please try again.'
    - Marks OTP as used upon successful verification.
    """
    clean_email = email.strip().lower()
    clean_otp = otp_code.strip()
    now = time.time()

    if not clean_otp:
        return False, "Please enter the 6-digit OTP."

    with get_connection() as conn:
        cursor = conn.cursor()
        if purpose:
            cursor.execute(
                """
                SELECT id, otp_code, expires_at, used, attempts, purpose 
                FROM otps 
                WHERE LOWER(email) = ? AND purpose = ?
                ORDER BY id DESC LIMIT 1
                """,
                (clean_email, purpose)
            )
        else:
            cursor.execute(
                """
                SELECT id, otp_code, expires_at, used, attempts, purpose 
                FROM otps 
                WHERE LOWER(email) = ? 
                ORDER BY id DESC LIMIT 1
                """,
                (clean_email,)
            )
        row = cursor.fetchone()

        if not row:
            return False, "No OTP request found for this email. Please request a new OTP."

        if row["used"] == 1:
            return False, "This OTP has already been used. Please request a fresh OTP."

        if now > row["expires_at"]:
            return False, "The OTP has expired. Please request a new OTP."

        current_attempts = row["attempts"] if row["attempts"] is not None else 0

        # Check if already locked out
        if current_attempts >= MAX_OTP_ATTEMPTS:
            cursor.execute("UPDATE otps SET used = 1 WHERE id = ?", (row["id"],))
            conn.commit()
            return False, "Maximum incorrect attempts exceeded. This OTP has been invalidated. Please request a new OTP."

        # Check if OTP matches
        if row["otp_code"] != clean_otp:
            new_attempts = current_attempts + 1
            if new_attempts >= MAX_OTP_ATTEMPTS:
                cursor.execute("UPDATE otps SET attempts = ?, used = 1 WHERE id = ?", (new_attempts, row["id"]))
                conn.commit()
                return False, "Invalid OTP. Maximum attempts exceeded. Please request a new OTP."
            else:
                cursor.execute("UPDATE otps SET attempts = ? WHERE id = ?", (new_attempts, row["id"]))
                conn.commit()
                return False, "Invalid OTP. Please try again."

        # Success: consume OTP
        cursor.execute("UPDATE otps SET used = 1 WHERE id = ?", (row["id"],))
        conn.commit()
        return True, "OTP verified successfully!"

def get_latest_otp_info(email: str, purpose: str = "login") -> Optional[Dict]:
    """Retrieves metadata of the latest OTP without revealing the raw code."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, expires_at, used, attempts, purpose, created_at
            FROM otps
            WHERE LOWER(email) = LOWER(?) AND purpose = ?
            ORDER BY id DESC LIMIT 1
            """,
            (email.strip(), purpose)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

# ==============================================================================
# FRANCHISE MANAGEMENT DATA OPERATIONS
# ==============================================================================

def get_all_franchises(owner_filter: Optional[str] = None) -> List[Dict]:
    """Retrieves franchise outlets list, optionally filtered by owner username."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if owner_filter:
            cursor.execute(
                "SELECT * FROM franchises WHERE LOWER(owner_username) = LOWER(?) ORDER BY id ASC",
                (owner_filter.strip(),)
            )
        else:
            cursor.execute("SELECT * FROM franchises ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_franchise_by_code(code: str) -> Optional[Dict]:
    """Fetches single franchise outlet by unique code."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM franchises WHERE UPPER(code) = UPPER(?)", (code.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_franchise_orders(franchise_code: Optional[str] = None) -> List[Dict]:
    """Fetches supply orders for all or a specific franchise."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if franchise_code:
            cursor.execute(
                "SELECT * FROM franchise_orders WHERE UPPER(franchise_code) = UPPER(?) ORDER BY id DESC",
                (franchise_code.strip(),)
            )
        else:
            cursor.execute("SELECT * FROM franchise_orders ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def create_franchise_order(franchise_code: str, item_name: str, quantity: int) -> bool:
    """Places a new inventory supply request for a franchise outlet."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO franchise_orders (franchise_code, item_name, quantity, status) VALUES (?, ?, ?, 'Processing')",
                (franchise_code.strip().upper(), item_name.strip(), quantity)
            )
            conn.commit()
            return True
    except Exception:
        return False

def submit_franchise_application(name: str, email: str, phone: str, city: str, budget: str) -> bool:
    """Stores a new franchise application request."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO franchise_applications (applicant_name, email, phone, city, budget, status)
                VALUES (?, ?, ?, ?, ?, 'Under Review')
                """,
                (name.strip(), email.strip().lower(), phone.strip(), city.strip(), budget.strip())
            )
            conn.commit()
            return True
    except Exception:
        return False

def get_all_franchise_applications() -> List[Dict]:
    """Fetches all submitted franchise license applications for administrative review."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM franchise_applications ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
