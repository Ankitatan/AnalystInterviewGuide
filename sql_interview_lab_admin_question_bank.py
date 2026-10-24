
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import secrets
import hmac
import re
import json
from pathlib import Path
from datetime import datetime, timezone

import requests
from urllib.parse import urlencode


# ============================================================
# SQL INTERVIEW LAB — COMPLETE SINGLE-FILE APPLICATION
# ============================================================

st.set_page_config(
    page_title="SQL Interview Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

#------Add GitHub verification code-----#
def github_owner_authorized():
    return st.session_state.get("github_owner_verified", False)


def github_authorization_url():
    state = secrets.token_urlsafe(32)
    st.session_state["github_oauth_state"] = state

    params = {
        "client_id": st.secrets["github"]["client_id"],
        "redirect_uri": st.secrets["github"]["redirect_uri"],
        "scope": "read:user",
        "state": state,
    }

    return (
        "https://github.com/login/oauth/authorize?"
        + urlencode(params)
    )


def process_github_callback():
    code = st.query_params.get("code")
    returned_state = st.query_params.get("state")

    if not code:
        return

    expected_state = st.session_state.get("github_oauth_state")

    # Verify OAuth state to help prevent request forgery.
    if not expected_state or not hmac.compare_digest(
        str(returned_state or ""),
        str(expected_state),
    ):
        st.session_state["github_owner_verified"] = False
        st.error("GitHub authorization could not be verified.")
        st.query_params.clear()
        return

    try:
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": st.secrets["github"]["client_id"],
                "client_secret": st.secrets["github"]["client_secret"],
                "code": code,
                "redirect_uri": st.secrets["github"]["redirect_uri"],
            },
            timeout=15,
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError("GitHub did not return an access token.")

        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15,
        )
        user_response.raise_for_status()
        github_user = user_response.json()

        expected_owner = st.secrets["github"]["owner_username"]

        if github_user.get("login", "").casefold() == expected_owner.casefold():
            st.session_state["github_owner_verified"] = True
            st.session_state["github_owner_login"] = github_user["login"]
            st.session_state.pop("github_oauth_state", None)
            st.success("GitHub owner verified.")
        else:
            st.session_state["github_owner_verified"] = False
            st.error(
                "Permission denied. Only the designated GitHub owner "
                "can authorize administrator creation."
            )

    except Exception as exc:
        st.session_state["github_owner_verified"] = False
        st.error(f"GitHub authorization failed: {exc}")

    finally:
        st.query_params.clear()


process_github_callback()


# -------------------- Paths and Theme --------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CSV_DIR = DATA_DIR / "uploaded_csv"
QUESTION_DB = DATA_DIR / "question_bank.db"
UPLOADED_DB = DATA_DIR / "uploaded_database.db"
SAMPLE_DB = DATA_DIR / "sample_database.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary-color: #6d5dfc;
    --ink: #262344;
    --muted: #77748e;
    --border: #e9e6f5;
    --surface: #ffffff;
    --lavender: #f5f3ff;
}

.stApp {
    background: linear-gradient(135deg, #faf9ff 0%, #f5f7ff 100%);
    font-family: 'Inter', sans-serif;
    color: var(--ink);
}

[data-testid="stHeader"] {
    background: rgba(250, 249, 255, 0.9);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #211b46 0%, #302765 100%);
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #ffffff;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #e1ddff;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 7px 10px;
    border-radius: 8px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255, 255, 255, 0.12);
}

h1, h2, h3 {
    color: #302765;
    font-weight: 750;
    letter-spacing: -0.5px;
}

h1 {
    font-size: 2.15rem;
}

p, label, .stMarkdown {
    line-height: 1.65;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid var(--border);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 18px rgba(48, 39, 101, 0.04);
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #302765;
    font-weight: 800;
}

div.stButton > button,
div.stDownloadButton > button,
.stLinkButton a {
    border-radius: 10px;
    font-weight: 600;
    min-height: 42px;
    transition: all 0.2s ease;
}

div.stButton > button[kind="primary"] {
    background: #6d5dfc;
    border: 1px solid #6d5dfc;
    color: white;
}

div.stButton > button[kind="primary"]:hover {
    background: #5545e8;
    border-color: #5545e8;
    box-shadow: 0 5px 14px rgba(109, 93, 252, 0.25);
}

div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 13px;
    overflow: hidden;
}

div[data-testid="stExpander"] summary {
    font-weight: 600;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox [data-baseweb="select"] > div {
    border-radius: 9px;
}

.stTextArea textarea {
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.65;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

hr {
    border-color: var(--border);
}

div[data-testid="stAlert"] {
    border-radius: 11px;
}

div[data-testid="stTabs"] button {
    font-weight: 600;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# -------------------- Unified Login Session --------------------

SESSION_DEFAULTS = {
    "logged_in": False,
    "username": "",
    "role": "",
    "question_admin_authenticated": False,
    "question_admin_name": "",
}

for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def set_login_session(username, role="admin"):
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.role = role
    st.session_state.question_admin_authenticated = True
    st.session_state.question_admin_name = username


def clear_login_session():
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value

    st.session_state.pop("login_error", None)

def clear_editor(editor_key):
    st.session_state[editor_key] = ""

# -------------------- Question Bank Database --------------------

def get_question_connection():
    conn = sqlite3.connect(QUESTION_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_question_database():
    conn = get_question_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL DEFAULT 'Basic',
            topic TEXT NOT NULL DEFAULT 'General',
            title TEXT NOT NULL DEFAULT '',
            prompt TEXT NOT NULL DEFAULT '',
            hint TEXT NOT NULL DEFAULT '',
            solution TEXT NOT NULL DEFAULT '',
            explanation TEXT NOT NULL DEFAULT '',
            expected_rows INTEGER NOT NULL DEFAULT 0,
            database_name TEXT NOT NULL DEFAULT 'Sample database',
            contributor_github TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL DEFAULT '',
            updated_by TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT ''
        )
    """)

    # Add missing columns when opening an older question bank.
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(questions)").fetchall()
    }

    migrations = {
        "level": "TEXT NOT NULL DEFAULT 'Basic'",
        "topic": "TEXT NOT NULL DEFAULT 'General'",
        "title": "TEXT NOT NULL DEFAULT ''",
        "prompt": "TEXT NOT NULL DEFAULT ''",
        "hint": "TEXT NOT NULL DEFAULT ''",
        "solution": "TEXT NOT NULL DEFAULT ''",
        "explanation": "TEXT NOT NULL DEFAULT ''",
        "expected_rows": "INTEGER NOT NULL DEFAULT 0",
        "database_name": "TEXT NOT NULL DEFAULT 'Sample database'",
        "contributor_github": "TEXT NOT NULL DEFAULT ''",
        "created_by": "TEXT NOT NULL DEFAULT ''",
        "updated_by": "TEXT NOT NULL DEFAULT ''",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }

    for column, definition in migrations.items():
        if column not in columns:
            conn.execute(
                f"ALTER TABLE questions ADD COLUMN {column} {definition}"
            )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            last_attempt TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (username, question_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT '',
            UNIQUE(username, question_id)
        )
    """)

    now = utc_now()
    conn.execute(
        "UPDATE questions SET created_at=? WHERE created_at=''",
        (now,),
    )
    conn.execute(
        "UPDATE questions SET updated_at=? WHERE updated_at=''",
        (now,),
    )

    conn.commit()
    conn.close()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000,
    ).hex()
    return password_hash, salt


def admin_count():
    conn = get_question_connection()
    count = conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    conn.close()
    return count


def create_admin(username, password):
    password_hash, salt = hash_password(password)
    conn = get_question_connection()
    try:
        conn.execute(
            """
            INSERT INTO admins
            (username, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, password_hash, salt, utc_now()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_admin(username, password):
    conn = get_question_connection()
    row = conn.execute(
        """
        SELECT username, password_hash, salt
        FROM admins
        WHERE username = ? COLLATE NOCASE
        """,
        (username,),
    ).fetchone()
    conn.close()

    if not row:
        return False

    candidate_hash, _ = hash_password(password, row["salt"])
    return hmac.compare_digest(candidate_hash, row["password_hash"])


# -------------------- Sample Database --------------------

def init_sample_database():
    conn = sqlite3.connect(SAMPLE_DB)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT,
            city TEXT,
            country TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            amount REAL,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name TEXT,
            department TEXT,
            salary REAL,
            manager_id INTEGER
        );
    """)

    existing = conn.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    if existing == 0:
        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            [
                (1, "Aarav Sharma", "Delhi", "India"),
                (2, "Priya Singh", "Mumbai", "India"),
                (3, "Rohan Mehta", "Pune", "India"),
                (4, "Sara Khan", "Delhi", "India"),
                (5, "Neha Verma", "Bengaluru", "India"),
                (6, "John Smith", "London", "UK"),
            ],
        )

        conn.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
            [
                (101, 1, "2026-01-03", 2500, "Completed"),
                (102, 2, "2026-01-05", 1800, "Completed"),
                (103, 1, "2026-01-11", 4200, "Pending"),
                (104, 3, "2026-02-02", 3100, "Completed"),
                (105, 4, "2026-02-09", 900, "Cancelled"),
                (106, 5, "2026-02-15", 5500, "Completed"),
                (107, 2, "2026-03-01", 1200, "Pending"),
                (108, 6, "2026-03-12", 2700, "Completed"),
            ],
        )

        conn.executemany(
            "INSERT INTO employees VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Aarav", "Analytics", 65000, None),
                (2, "Priya", "Analytics", 72000, 1),
                (3, "Rohan", "Engineering", 85000, None),
                (4, "Sara", "HR", 58000, None),
                (5, "Neha", "Engineering", 79000, 3),
                (6, "John", "Sales", 62000, None),
            ],
        )

    conn.commit()
    conn.close()


# -------------------- Uploaded CSV Database --------------------

def sync_uploaded_database():
    """Rebuild the uploaded SQLite database from saved CSV files."""
    if UPLOADED_DB.exists():
        UPLOADED_DB.unlink()

    conn = sqlite3.connect(UPLOADED_DB)

    try:
        for csv_file in sorted(CSV_DIR.glob("*.csv")):
            table_name = re.sub(
                r"[^a-zA-Z0-9_]", "_", csv_file.stem
            ).strip("_")

            if not table_name:
                continue

            try:
                frame = pd.read_csv(csv_file, low_memory=False)
                frame.columns = [
                    str(c).strip() or f"column_{i}"
                    for i, c in enumerate(frame.columns)
                ]
                frame.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False,
                )
            except Exception as exc:
                st.warning(f"Could not load {csv_file.name}: {exc}")
    finally:
        conn.close()

def get_tables(database_name):
    if database_name == "Sample database":
        db_path = SAMPLE_DB
    else:
        db_path = UPLOADED_DB

    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()
    conn.close()
    return [row[0] for row in rows]


def connect_for_database(database_name):
    if database_name == "Sample database":
        return sqlite3.connect(SAMPLE_DB, timeout=30)
    return sqlite3.connect(UPLOADED_DB, timeout=30)


# -------------------- Read-Only SQL Safety --------------------

DENIED_SQL_ACTIONS = {
    getattr(sqlite3, name)
    for name in [
        "SQLITE_INSERT",
        "SQLITE_UPDATE",
        "SQLITE_DELETE",
        "SQLITE_CREATE_INDEX",
        "SQLITE_CREATE_TABLE",
        "SQLITE_CREATE_TEMP_INDEX",
        "SQLITE_CREATE_TEMP_TABLE",
        "SQLITE_CREATE_TEMP_TRIGGER",
        "SQLITE_CREATE_TEMP_VIEW",
        "SQLITE_CREATE_TRIGGER",
        "SQLITE_CREATE_VIEW",
        "SQLITE_DROP_INDEX",
        "SQLITE_DROP_TABLE",
        "SQLITE_DROP_TEMP_INDEX",
        "SQLITE_DROP_TEMP_TABLE",
        "SQLITE_DROP_TEMP_TRIGGER",
        "SQLITE_DROP_TEMP_VIEW",
        "SQLITE_DROP_TRIGGER",
        "SQLITE_DROP_VIEW",
        "SQLITE_ALTER_TABLE",
        "SQLITE_ATTACH",
        "SQLITE_DETACH",
        "SQLITE_PRAGMA",
        "SQLITE_REINDEX",
        "SQLITE_ANALYZE",
    ]
    if hasattr(sqlite3, name)
}


def read_only_authorizer(action, arg1, arg2, database_name, trigger_name):
    if action in DENIED_SQL_ACTIONS:
        return sqlite3.SQLITE_DENY

    # Prevent reading SQLite's internal schema tables directly.
    if arg1 and str(arg1).startswith("sqlite_"):
        return sqlite3.SQLITE_DENY

    return sqlite3.SQLITE_OK


def run_read_only_query(database_name, sql):
    cleaned = sql.strip().rstrip(";")

    if not cleaned:
        raise ValueError("Enter a SQL query first.")

    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", cleaned, re.I):
        raise ValueError(
            "Only SELECT, WITH, or EXPLAIN queries are allowed."
        )

    conn = connect_for_database(database_name)
    try:
        conn.set_authorizer(read_only_authorizer)
        return pd.read_sql_query(cleaned, conn)
    finally:
        conn.close()


# -------------------- Starter Questions --------------------

OLIST_QUESTIONS = [
    {
        "level": "Basic",
        "topic": "Filtering",
        "title": "Find Delivered Orders",
        "prompt": (
            "Using olist_orders_dataset, return order_id, customer_id, "
            "and order_status for delivered orders."
        ),
        "hint": "Use WHERE to filter order_status.",
        "solution": """
SELECT order_id, customer_id, order_status
FROM olist_orders_dataset
WHERE order_status = 'delivered';
""".strip(),
        "explanation": (
            "WHERE filters the orders to only those with delivered status."
        ),
    },
    {
        "level": "Basic",
        "topic": "Aggregation",
        "title": "Count Orders by Status",
        "prompt": (
            "Count the number of orders in each order_status category."
        ),
        "hint": "Use GROUP BY with COUNT(*).",
        "solution": """
SELECT order_status, COUNT(*) AS order_count
FROM olist_orders_dataset
GROUP BY order_status
ORDER BY order_count DESC;
""".strip(),
        "explanation": (
            "GROUP BY creates one group per status; COUNT counts rows."
        ),
    },
    {
        "level": "Intermediate",
        "topic": "Date Analysis",
        "title": "Orders by Purchase Month",
        "prompt": (
            "Count orders by purchase month using order_purchase_timestamp."
        ),
        "hint": "SQLite's strftime('%Y-%m', ...) extracts year and month.",
        "solution": """
SELECT
    strftime('%Y-%m', order_purchase_timestamp) AS purchase_month,
    COUNT(*) AS order_count
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
GROUP BY purchase_month
ORDER BY purchase_month;
""".strip(),
        "explanation": (
            "strftime extracts the month; grouping aggregates orders "
            "for each month."
        ),
    },
    {
        "level": "Intermediate",
        "topic": "Date Analysis",
        "title": "Late Delivered Orders",
        "prompt": (
            "Find delivered orders where the actual delivery timestamp "
            "is later than the estimated delivery timestamp."
        ),
        "hint": (
            "Compare order_delivered_customer_date with "
            "order_estimated_delivery_date."
        ),
        "solution": """
SELECT
    order_id,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM olist_orders_dataset
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL
  AND order_delivered_customer_date > order_estimated_delivery_date;
""".strip(),
        "explanation": (
            "Comparing the two timestamps identifies orders delivered "
            "after the estimated date."
        ),
    },
    {
        "level": "Expert",
        "topic": "Window Functions",
        "title": "Rank Orders by Purchase Date",
        "prompt": (
            "Rank orders from newest to oldest using "
            "order_purchase_timestamp."
        ),
        "hint": "Use ROW_NUMBER() OVER (ORDER BY ... DESC).",
        "solution": """
SELECT
    order_id,
    order_purchase_timestamp,
    ROW_NUMBER() OVER (
        ORDER BY order_purchase_timestamp DESC
    ) AS purchase_rank
FROM olist_orders_dataset;
""".strip(),
        "explanation": (
            "ROW_NUMBER assigns a unique sequential rank based on "
            "descending purchase timestamp."
        ),
    },
    {
        "level": "Expert",
        "topic": "Common Table Expressions",
        "title": "Summarize Monthly Order Volume",
        "prompt": (
            "Use a CTE to count orders per month and return months "
            "with more than 1,000 orders."
        ),
        "hint": "Build the monthly summary in a WITH clause.",
        "solution": """
WITH monthly_orders AS (
    SELECT
        strftime('%Y-%m', order_purchase_timestamp) AS purchase_month,
        COUNT(*) AS order_count
    FROM olist_orders_dataset
    WHERE order_purchase_timestamp IS NOT NULL
    GROUP BY strftime('%Y-%m', order_purchase_timestamp)
)
SELECT purchase_month, order_count
FROM monthly_orders
WHERE order_count > 1000
ORDER BY purchase_month;
""".strip(),
        "explanation": (
            "The CTE creates a monthly summary; the outer query filters "
            "months with more than 1,000 orders."
        ),
    },
]


ADDITIONAL_OLIST_QUESTIONS = [
    {
        "level": "Basic",
        "topic": "Filtering",
        "title": "Find Cancelled Orders",
        "prompt": "Find all orders with order_status = 'canceled'. Return order_id, customer_id, and order_status.",
        "hint": "Use WHERE to filter order_status.",
        "solution": """SELECT order_id, customer_id, order_status
FROM olist_orders_dataset
WHERE order_status = 'canceled';""",
        "explanation": "WHERE filters the table to cancelled orders.",
    },
    {
        "level": "Basic",
        "topic": "NULL Handling",
        "title": "Find Orders Without Approval",
        "prompt": "Find orders with a purchase timestamp but no approval timestamp.",
        "hint": "Use IS NULL.",
        "solution": """SELECT order_id, order_status, order_purchase_timestamp
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
  AND order_approved_at IS NULL;""",
        "explanation": "IS NULL finds records with missing approval timestamps.",
    },
    {
        "level": "Intermediate",
        "topic": "HAVING",
        "title": "Order Statuses with More Than 1000 Orders",
        "prompt": "Return statuses with more than 1000 orders.",
        "hint": "Use HAVING COUNT(*) > 1000.",
        "solution": """SELECT order_status, COUNT(*) AS total_orders
FROM olist_orders_dataset
GROUP BY order_status
HAVING COUNT(*) > 1000
ORDER BY total_orders DESC;""",
        "explanation": "HAVING filters groups after aggregation.",
    },
    {
        "level": "Intermediate",
        "topic": "Date Analysis",
        "title": "Orders by Purchase Year",
        "prompt": "Count orders by purchase year in chronological order.",
        "hint": "Use strftime('%Y', order_purchase_timestamp).",
        "solution": """SELECT strftime('%Y', order_purchase_timestamp) AS purchase_year,
       COUNT(*) AS total_orders
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
GROUP BY strftime('%Y', order_purchase_timestamp)
ORDER BY purchase_year;""",
        "explanation": "strftime extracts the year, and GROUP BY calculates yearly counts.",
    },
    {
        "level": "Intermediate",
        "topic": "Date Analysis",
        "title": "Average Delivery Days",
        "prompt": "Calculate the average days between purchase and customer delivery for each order status.",
        "hint": "Subtract julianday(purchase timestamp) from julianday(delivery timestamp).",
        "solution": """SELECT order_status,
       ROUND(AVG(
           julianday(order_delivered_customer_date)
           - julianday(order_purchase_timestamp)
       ), 2) AS average_delivery_days
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
  AND order_delivered_customer_date IS NOT NULL
GROUP BY order_status
ORDER BY average_delivery_days DESC;""",
        "explanation": "The difference between Julian day values measures elapsed days.",
    },
    {
        "level": "Intermediate",
        "topic": "CASE Expressions",
        "title": "Classify Delivery Performance",
        "prompt": "Classify orders with actual and estimated delivery dates as Early, On Time, or Late. Count each category.",
        "hint": "Use CASE and compare the two delivery dates.",
        "solution": """WITH classified AS (
    SELECT CASE
        WHEN julianday(order_delivered_customer_date)
             < julianday(order_estimated_delivery_date) THEN 'Early'
        WHEN julianday(order_delivered_customer_date)
             = julianday(order_estimated_delivery_date) THEN 'On Time'
        ELSE 'Late'
    END AS delivery_category
    FROM olist_orders_dataset
    WHERE order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
)
SELECT delivery_category, COUNT(*) AS total_orders
FROM classified
GROUP BY delivery_category
ORDER BY total_orders DESC;""",
        "explanation": "CASE assigns a delivery category to each eligible order.",
    },
    {
        "level": "Intermediate",
        "topic": "Subqueries and CTEs",
        "title": "Find the Busiest Purchase Day",
        "prompt": "Find the calendar date with the most orders and return its date and order count.",
        "hint": "Group by DATE(order_purchase_timestamp), then sort by count descending and limit to one.",
        "solution": """SELECT DATE(order_purchase_timestamp) AS purchase_date,
       COUNT(*) AS total_orders
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
GROUP BY DATE(order_purchase_timestamp)
ORDER BY total_orders DESC, purchase_date
LIMIT 1;""",
        "explanation": "Grouping by calendar date identifies the day with the highest order volume.",
    },
    {
        "level": "Expert",
        "topic": "Window Functions",
        "title": "Rank Orders Within Each Status",
        "prompt": "Rank orders by purchase timestamp, oldest first, restarting the rank for each order status.",
        "hint": "Use ROW_NUMBER() OVER (PARTITION BY order_status ...).",
        "solution": """SELECT order_id,
       order_status,
       order_purchase_timestamp,
       ROW_NUMBER() OVER (
           PARTITION BY order_status
           ORDER BY order_purchase_timestamp, order_id
       ) AS status_rank
FROM olist_orders_dataset
WHERE order_purchase_timestamp IS NOT NULL
ORDER BY order_status, status_rank;""",
        "explanation": "PARTITION BY restarts ranking for each status.",
    },
    {
        "level": "Expert",
        "topic": "Window Functions",
        "title": "Cumulative Monthly Orders",
        "prompt": "Calculate monthly order counts and a cumulative running total ordered by purchase month.",
        "hint": "Aggregate monthly orders in a CTE, then use SUM() OVER (ORDER BY purchase_month).",
        "solution": """WITH monthly AS (
    SELECT strftime('%Y-%m', order_purchase_timestamp) AS purchase_month,
           COUNT(*) AS monthly_orders
    FROM olist_orders_dataset
    WHERE order_purchase_timestamp IS NOT NULL
    GROUP BY strftime('%Y-%m', order_purchase_timestamp)
)
SELECT purchase_month,
       monthly_orders,
       SUM(monthly_orders) OVER (
           ORDER BY purchase_month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_orders
FROM monthly
ORDER BY purchase_month;""",
        "explanation": "The window SUM accumulates the current month's count and all preceding months.",
    },
    {
        "level": "Intermediate",
        "topic": "Data Quality",
        "title": "Find Duplicate Order IDs",
        "prompt": "Identify order IDs that appear more than once.",
        "hint": "Group by order_id and use HAVING COUNT(*) > 1.",
        "solution": """SELECT order_id, COUNT(*) AS record_count
FROM olist_orders_dataset
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY record_count DESC;""",
        "explanation": "This query checks whether order identifiers are duplicated.",
    },
    {
        "level": "Expert",
        "topic": "Conditional Aggregation",
        "title": "Monthly Late Delivery Percentage",
        "prompt": "For each purchase month, calculate eligible delivered orders, late orders, and late delivery percentage.",
        "hint": "Use a CTE and conditional SUM with CASE.",
        "solution": """WITH eligible AS (
    SELECT strftime('%Y-%m', order_purchase_timestamp) AS purchase_month,
           CASE
               WHEN julianday(order_delivered_customer_date)
                    > julianday(order_estimated_delivery_date)
               THEN 1 ELSE 0
           END AS is_late
    FROM olist_orders_dataset
    WHERE order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
)
SELECT purchase_month,
       COUNT(*) AS eligible_orders,
       SUM(is_late) AS late_orders,
       ROUND(100.0 * SUM(is_late) / COUNT(*), 2) AS late_percentage
FROM eligible
GROUP BY purchase_month
ORDER BY purchase_month;""",
        "explanation": "Conditional aggregation calculates the number and percentage of late deliveries for each month.",
    },
]


# Combine the original six with the twelve new questions.
OLIST_QUESTIONS.extend(ADDITIONAL_OLIST_QUESTIONS)



def seed_starter_questions():
    conn = get_question_connection()
    now = utc_now()

    for item in OLIST_QUESTIONS:
        exists = conn.execute(
            """
            SELECT 1
            FROM questions
            WHERE title = ?
              AND database_name = ?
            LIMIT 1
            """,
            (item["title"], "Uploaded CSV database"),
        ).fetchone()

        if exists:
            continue

        conn.execute(
            """
            INSERT INTO questions (
                level, topic, title, prompt, hint, solution,
                explanation, expected_rows, database_name,
                contributor_github, created_by, updated_by,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["level"],
                item["topic"],
                item["title"],
                item["prompt"],
                item["hint"],
                item["solution"],
                item["explanation"],
                "Uploaded CSV database",
                "Ankitatan",
                "system",
                "system",
                now,
                now,
            ),
        )

    conn.commit()
    conn.close()


def load_questions():
    conn = get_question_connection()
    rows = conn.execute(
        "SELECT * FROM questions ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_question(data, question_id=None):
    conn = get_question_connection()
    now = utc_now()

    if question_id is None:
        conn.execute("""
            INSERT INTO questions (
                level, topic, title, prompt, hint, solution,
                explanation, expected_rows, database_name,
                contributor_github, created_by, updated_by,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["level"], data["topic"], data["title"],
            data["prompt"], data["hint"], data["solution"],
            data["explanation"], data["expected_rows"],
            data["database_name"], data["contributor_github"],
            st.session_state.username, st.session_state.username,
            now, now,
        ))
    else:
        conn.execute("""
            UPDATE questions SET
                level=?, topic=?, title=?, prompt=?, hint=?,
                solution=?, explanation=?, expected_rows=?,
                database_name=?, contributor_github=?,
                updated_by=?, updated_at=?
            WHERE id=?
        """, (
            data["level"], data["topic"], data["title"],
            data["prompt"], data["hint"], data["solution"],
            data["explanation"], data["expected_rows"],
            data["database_name"], data["contributor_github"],
            st.session_state.username, now, question_id,
        ))

    conn.commit()
    conn.close()


def delete_question(question_id):
    conn = get_question_connection()
    conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
    conn.execute("DELETE FROM progress WHERE question_id=?", (question_id,))
    conn.execute("DELETE FROM notes WHERE question_id=?", (question_id,))
    conn.commit()
    conn.close()


def get_completed_ids(username):
    conn = get_question_connection()
    rows = conn.execute(
        "SELECT question_id FROM progress WHERE username=? AND completed=1",
        (username,),
    ).fetchall()
    conn.close()
    return {row[0] for row in rows}


def mark_question_completed(username, question_id):
    conn = get_question_connection()
    conn.execute("""
        INSERT INTO progress (username, question_id, completed, last_attempt)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(username, question_id)
        DO UPDATE SET completed=1, last_attempt=excluded.last_attempt
    """, (username, question_id, utc_now()))
    conn.commit()
    conn.close()


def save_note(username, question_id, note):
    conn = get_question_connection()
    conn.execute("""
        INSERT INTO notes (username, question_id, note, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username, question_id)
        DO UPDATE SET note=excluded.note, updated_at=excluded.updated_at
    """, (username, question_id, note, utc_now()))
    conn.commit()
    conn.close()


def get_note(username, question_id):
    conn = get_question_connection()
    row = conn.execute(
        "SELECT note FROM notes WHERE username=? AND question_id=?",
        (username, question_id),
    ).fetchone()
    conn.close()
    return row[0] if row else ""


# -------------------- Initialize App Data --------------------

init_question_database()
init_sample_database()
sync_uploaded_database()
seed_starter_questions()


#------this rebuild deletes the existing uploaded SQLite database before importing the CSVs-----#

def sync_uploaded_database():
    """Rebuild the uploaded SQLite database from saved CSV files."""
    if UPLOADED_DB.exists():
        UPLOADED_DB.unlink()

    conn = sqlite3.connect(UPLOADED_DB)

    try:
        for csv_file in sorted(CSV_DIR.glob("*.csv")):
            table_name = re.sub(
                r"[^a-zA-Z0-9_]", "_", csv_file.stem
            ).strip("_")

            if not table_name:
                continue

            try:
                frame = pd.read_csv(csv_file, low_memory=False)
                frame.columns = [
                    str(c).strip() or f"column_{i}"
                    for i, c in enumerate(frame.columns)
                ]

                frame.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False,
                )
            except Exception as exc:
                st.warning(
                    f"Could not load {csv_file.name}: {exc}"
                )

    finally:
        conn.close()

# -------------------- Sidebar Navigation --------------------

st.sidebar.title("🧪 SQL Interview Lab")
st.sidebar.caption("Practice SQL. Explore data. Track progress.")

pages = [
    "Home",
    "Practice Lab",
    "Question Management",
    "Explore Data",
    "Dataset Manager",
    "Progress & Notes",
    "About",
]

if "home_navigation" in st.session_state:
    default_page = st.session_state.pop("home_navigation")
else:
    default_page = "Home"

page = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(default_page) if default_page in pages else 0,
)

if st.session_state.logged_in:
    st.sidebar.success(f"Signed in: {st.session_state.username}")
    if st.sidebar.button("Sign out", key="sidebar_signout",
                          use_container_width=True):
        clear_login_session()
        st.rerun()
else:
    st.sidebar.caption("Not signed in")

# -------------------- Home --------------------

if page == "Home":
    st.title("SQL Interview Lab")
    st.markdown(
        "### Practice SQL. Build confidence. Prepare for interviews."
    )
    st.write(
        "Explore SQL challenges, work with real datasets, "
        "and strengthen your analytical thinking."
    )

    questions = load_questions()
    completed = (
        get_completed_ids(st.session_state.username)
        if st.session_state.logged_in else set()
    )
    csv_count = len(list(CSV_DIR.glob("*.csv")))

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("SQL Questions", len(questions))
    col2.metric("Completed", len(completed))
    col3.metric("Remaining", max(len(questions) - len(completed), 0))
    col4.metric("CSV Datasets", csv_count)

    st.write("")
    st.subheader("Your Learning Workspace")

    left, right = st.columns([1.4, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("#### 🧠 Practice SQL")
            st.write(
                "Solve questions from Basic to Expert. "
                "Use hints, execute queries, and review solutions."
            )
            st.caption("Filtering · Joins · Aggregations · Window functions")
            if st.button(
                "Open Practice Lab →",
                key="home_practice",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["home_navigation"] = "Practice Lab"
                st.rerun()

        with st.container(border=True):
            st.markdown("#### 📊 Explore Your Data")
            st.write(
                "Upload CSV files, inspect table structures, "
                "and explore columns before writing SQL."
            )
            if st.button(
                "Manage Datasets →",
                key="home_datasets",
                use_container_width=True,
            ):
                st.session_state["home_navigation"] = "Dataset Manager"
                st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("#### 🎯 Learning Progress")
            if questions:
                percentage = min(
                    100, round(100 * len(completed) / len(questions))
                )
            else:
                percentage = 0

            st.progress(percentage / 100)
            st.markdown(f"**{percentage}% completed**")
            st.caption(
                "Sign in through Question Management to save "
                "your progress and personal notes."
            )

        with st.container(border=True):
            st.markdown("#### 💡 SQL Tip")
            st.write(
                "Start with a small SELECT query. Add WHERE filters, "
                "then GROUP BY or window functions as needed. "
                "Check your results at every step."
            )

    st.divider()
    st.subheader("Explore by Difficulty")

    basic, intermediate, expert = st.columns(3)

    for column, level, description in [
        (basic, "Basic", "Filtering, sorting, and simple aggregation."),
        (intermediate, "Intermediate", "Dates, HAVING, CASE, and subqueries."),
        (expert, "Expert", "CTEs, ranking, and window functions."),
    ]:
        with column:
            with st.container(border=True):
                st.markdown(f"#### {level}")
                count = sum(q["level"] == level for q in questions)
                st.metric("Available questions", count)
                st.caption(description)

    st.info(
        "The Olist starter questions require the "
        "`olist_orders_dataset` CSV. Upload it in Dataset Manager "
        "before running those solutions."
    )

# -------------------- Practice Lab --------------------

elif page == "Practice Lab":
    st.title("Practice Lab")

    questions = load_questions()

    if not questions:
        st.info("No questions available. Add questions in Question Management.")
    else:
        levels = ["All"] + sorted({q["level"] for q in questions})
        selected_level = st.selectbox("Filter by level", levels)

        filtered = [
            q for q in questions
            if selected_level == "All" or q["level"] == selected_level
        ]

        if not filtered:
            st.info("No questions match this filter.")

        for q in filtered:
            with st.expander(
                f'{q["level"]} · {q["title"]} | {q["topic"]}'
            ):
                st.write(q["prompt"])

                with st.expander("Show hint"):
                    st.write(q["hint"] or "No hint provided.")

                available_dbs = ["Sample database"]
                if get_tables("Uploaded CSV database"):
                    available_dbs.append("Uploaded CSV database")

                default_db = q["database_name"]
                if default_db not in available_dbs:
                    default_db = "Sample database"

                db_key = f"db_{q['id']}"
                if db_key not in st.session_state:
                    st.session_state[db_key] = default_db

                database_name = st.selectbox(
                    "Database",
                    available_dbs,
                    key=db_key,
                )

                with st.expander("Available tables"):
                    tables = get_tables(database_name)
                    st.write(
                        ", ".join(tables) if tables else "No tables found."
                    )

                editor_key = f"editor_{q['id']}"
                if editor_key not in st.session_state:
                    st.session_state[editor_key] = ""

                st.text_area(
                    "Write your SQL query",
                    key=editor_key,
                    height=180,
                    placeholder="SELECT * FROM customers;",
                )

                col_run, col_clear, col_solution = st.columns(3)

                with col_run:
                    run_clicked = st.button(
                        "▶ Run Query",
                        key=f"run_{q['id']}",
                        type="primary",
                        use_container_width=True,
                    )

                with col_clear:
                    st.button(
                        "Clear Editor",
                        key=f"clear_{q['id']}",
                        on_click=clear_editor,
                        args=(editor_key,),
                        use_container_width=True,
                    )

                with col_solution:
                    show_solution = st.button(
                        "Show Solution",
                        key=f"solution_{q['id']}",
                        use_container_width=True,
                    )

                # Persistent query state for this question
                success_key = f"query_succeeded_{q['id']}"
                result_key = f"query_result_{q['id']}"
                result_db_key = f"query_database_{q['id']}"

                if success_key not in st.session_state:
                    st.session_state[success_key] = False

                # Execute the query only when Run Query is clicked
                if run_clicked:
                    st.session_state[success_key] = False
                    st.session_state.pop(result_key, None)
                    st.session_state.pop(result_db_key, None)

                    try:
                        result = run_read_only_query(
                            database_name,
                            st.session_state[editor_key],
                        )
                        st.session_state[result_key] = result
                        st.session_state[result_db_key] = database_name
                        st.session_state[success_key] = True

                    except Exception as exc:
                        st.error(f"Query failed: {exc}")

                # Display the latest successful result after reruns
                if (
                    st.session_state[success_key]
                    and result_key in st.session_state
                ):
                    result = st.session_state[result_key]

                    if st.session_state.get(result_db_key) != database_name:
                        st.session_state[success_key] = False
                    else:
                        st.success(f"Query returned {len(result)} rows.")
                        st.dataframe(result, use_container_width=True)

                        if st.session_state.logged_in:
                            expected_rows = int(q["expected_rows"])

                            if (
                                expected_rows == 0
                                or len(result) == expected_rows
                            ):
                                if st.button(
                                    "Mark as Completed",
                                    key=f"complete_{q['id']}",
                                ):
                                    mark_question_completed(
                                        st.session_state.username,
                                        q["id"],
                                    )
                                    st.success("Progress saved.")
                                    st.rerun()
                            else:
                                st.caption(
                                    f"Expected {expected_rows} rows, "
                                    f"but your query returned {len(result)}. "
                                    "Review your result before marking "
                                    "this question complete."
                                )
                        else:
                            st.caption("Sign in to save your progress.")

                if show_solution:
                    st.code(q["solution"], language="sql")
                    st.markdown("**Explanation**")
                    st.write(q["explanation"])

                if st.session_state.logged_in:
                    with st.expander("My Notes"):
                        note_key = f"note_{q['id']}"

                        if note_key not in st.session_state:
                            st.session_state[note_key] = get_note(
                                st.session_state.username,
                                q["id"],
                            )

                        st.text_area(
                            "Notes for this question",
                            key=note_key,
                        )

                        if st.button(
                            "Save Notes",
                            key=f"save_note_{q['id']}",
                        ):
                            save_note(
                                st.session_state.username,
                                q["id"],
                                st.session_state[note_key],
                            )
                            st.success("Notes saved.")

# -------------------- Question Management --------------------

elif page == "Question Management":
    st.title("Question Management")

#-------Protect the first-admin setup-------#


    # First administrator setup: GitHub owner must authorize creation.
    if admin_count() == 0:
        st.subheader("Administrator Setup")
        st.write(
            "Verify the designated GitHub account before creating "
            "the first administrator."
        )

        if not github_owner_authorized():
            st.link_button(
                "Authorize with GitHub",
                github_authorization_url(),
                type="primary",
                use_container_width=True,
            )

            if st.session_state.get("login_error"):
                st.error(st.session_state["login_error"])

            st.stop()

        st.success(
            "Authorized GitHub account: "
            + st.session_state.get("github_owner_login", "")
        )

        with st.form("first_admin_form"):
            username = st.text_input("Admin username")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            create_clicked = st.form_submit_button(
                "Create Admin Account",
                use_container_width=True,
            )

        if create_clicked:
            username = username.strip()

            if not username or not password:
                st.error("Username and password are required.")
            elif len(password) < 10:
                st.error("Use a password with at least 10 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif create_admin(username, password):
                set_login_session(username)
                st.session_state.pop("login_error", None)
                st.rerun()
            else:
                st.error("That username already exists.")

        st.stop()

    # Existing administrators log in here.
    if not st.session_state.question_admin_authenticated:
        st.subheader("Admin Login")

        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

        if login_clicked:
            username = username.strip()

            if verify_admin(username, password):
                set_login_session(username)
                st.session_state.pop("login_error", None)
                st.rerun()
            else:
                st.session_state["login_error"] = (
                    "Incorrect username or password."
                )

        if st.session_state.get("login_error"):
            st.error(st.session_state["login_error"])

        st.stop()

    st.success(
        f"Authenticated as {st.session_state.question_admin_name}"
    )


    if st.button("Sign out of Question Management"):
        clear_login_session()
        st.rerun()

    st.divider()

    tab_add, tab_edit, tab_delete = st.tabs([
        "Add Question",
        "Edit Question",
        "Delete Question",
    ])

    available_databases = ["Sample database", "Uploaded CSV database"]

    with tab_add:
        st.subheader("Add a Question")

        with st.form("add_question_form"):
            level = st.selectbox(
                "Difficulty",
                ["Basic", "Intermediate", "Expert"],
            )
            topic = st.text_input("Topic")
            title = st.text_input("Question title")
            prompt = st.text_area("Question prompt")
            hint = st.text_area("Hint")
            solution = st.text_area("SQL solution")
            explanation = st.text_area("Explanation")
            database_name = st.selectbox(
                "Database",
                available_databases,
            )
            expected_rows = st.number_input(
                "Expected row count (0 = do not validate)",
                min_value=0,
                value=0,
                step=1,
            )
            contributor = st.text_input(
                "Contributor GitHub username",
                value="Ankitatan",
            )

            add_clicked = st.form_submit_button(
                "Add Question",
                type="primary",
            )

        if add_clicked:
            if not title.strip() or not prompt.strip():
                st.error("Title and prompt are required.")
            else:
                save_question({
                    "level": level,
                    "topic": topic.strip() or "General",
                    "title": title.strip(),
                    "prompt": prompt.strip(),
                    "hint": hint.strip(),
                    "solution": solution.strip(),
                    "explanation": explanation.strip(),
                    "expected_rows": int(expected_rows),
                    "database_name": database_name,
                    "contributor_github": contributor.strip(),
                })
                st.success("Question added.")
                st.rerun()

    questions = load_questions()

    with tab_edit:
        st.subheader("Edit an Existing Question")

        if questions:
            question_options = {
                f'{q["id"]} · {q["title"]}': q["id"]
                for q in questions
            }
            selected_label = st.selectbox(
                "Choose question",
                list(question_options.keys()),
                key="edit_question_choice",
            )
            selected_id = question_options[selected_label]
            selected_question = next(
                q for q in questions if q["id"] == selected_id
            )

            with st.form(f"edit_form_{selected_id}"):
                edit_level = st.selectbox(
                    "Difficulty",
                    ["Basic", "Intermediate", "Expert"],
                    index=["Basic", "Intermediate", "Expert"].index(
                        selected_question["level"]
                    ) if selected_question["level"] in
                    ["Basic", "Intermediate", "Expert"] else 0,
                )
                edit_topic = st.text_input(
                    "Topic",
                    value=selected_question["topic"],
                )
                edit_title = st.text_input(
                    "Title",
                    value=selected_question["title"],
                )
                edit_prompt = st.text_area(
                    "Prompt",
                    value=selected_question["prompt"],
                )
                edit_hint = st.text_area(
                    "Hint",
                    value=selected_question["hint"],
                )
                edit_solution = st.text_area(
                    "Solution",
                    value=selected_question["solution"],
                )
                edit_explanation = st.text_area(
                    "Explanation",
                    value=selected_question["explanation"],
                )
                db_index = available_databases.index(
                    selected_question["database_name"]
                ) if selected_question["database_name"] in available_databases else 0
                edit_database = st.selectbox(
                    "Database",
                    available_databases,
                    index=db_index,
                )
                edit_expected_rows = st.number_input(
                    "Expected row count (0 = do not validate)",
                    min_value=0,
                    value=int(selected_question["expected_rows"]),
                    step=1,
                )
                edit_contributor = st.text_input(
                    "Contributor GitHub username",
                    value=selected_question["contributor_github"],
                )

                edit_clicked = st.form_submit_button(
                    "Save Changes",
                    type="primary",
                )

            if edit_clicked:
                if not edit_title.strip() or not edit_prompt.strip():
                    st.error("Title and prompt are required.")
                else:
                    save_question({
                        "level": edit_level,
                        "topic": edit_topic.strip() or "General",
                        "title": edit_title.strip(),
                        "prompt": edit_prompt.strip(),
                        "hint": edit_hint.strip(),
                        "solution": edit_solution.strip(),
                        "explanation": edit_explanation.strip(),
                        "expected_rows": int(edit_expected_rows),
                        "database_name": edit_database,
                        "contributor_github": edit_contributor.strip(),
                    }, question_id=selected_id)
                    st.success("Question updated.")
                    st.rerun()
        else:
            st.info("No questions to edit.")

    with tab_delete:
        st.subheader("Delete a Question")

        if questions:
            delete_options = {
                f'{q["id"]} · {q["title"]}': q["id"]
                for q in questions
            }
            delete_label = st.selectbox(
                "Choose question to delete",
                list(delete_options.keys()),
                key="delete_question_choice",
            )
            delete_id = delete_options[delete_label]

            confirm_delete = st.checkbox(
                "I understand this permanently deletes the question "
                "and its saved progress and notes.",
                key="confirm_delete_question",
            )

            if st.button(
                "Delete Question",
                type="primary",
                disabled=not confirm_delete,
            ):
                delete_question(delete_id)
                st.success("Question deleted.")
                st.rerun()
        else:
            st.info("No questions to delete.")

    st.divider()
    st.subheader("Question Bank")

    questions = load_questions()
    if questions:
        bank_df = pd.DataFrame([
            {
                "ID": q["id"],
                "Level": q["level"],
                "Topic": q["topic"],
                "Title": q["title"],
                "Database": q["database_name"],
                "Contributor": q["contributor_github"],
                "Created by": q["created_by"],
                "Updated by": q["updated_by"],
            }
            for q in questions
        ])
        st.dataframe(bank_df, use_container_width=True, hide_index=True)

# -------------------- Dataset Manager --------------------

elif page == "Dataset Manager":
    st.title("Dataset Manager")
    st.write("Upload CSV datasets to create tables for SQL practice.")

    uploaded_files = st.file_uploader(
        "Upload one or more CSV files",
        type=["csv"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            safe_name = re.sub(
                r"[^a-zA-Z0-9_.-]",
                "_",
                Path(uploaded_file.name).name,
            )
            destination = CSV_DIR / safe_name

            if destination.exists():
                st.warning(
                    f"{safe_name} already exists and will be replaced."
                )

            destination.write_bytes(uploaded_file.getvalue())

        
    st.subheader("Uploaded CSV Files")

    csv_files = sorted(CSV_DIR.glob("*.csv"))

    if csv_files:
        for csv_file in csv_files:
            with st.expander(csv_file.name):
                try:
                    frame = pd.read_csv(csv_file, low_memory=False)
                    st.write(
                        f"Rows: {len(frame):,} · "
                        f"Columns: {len(frame.columns)}"
                    )
                    st.dataframe(frame.head(10), use_container_width=True)
                except Exception as exc:
                    st.error(f"Could not preview CSV: {exc}")

        st.divider()
        st.subheader("Delete Uploaded Files")

        selected_files = st.multiselect(
            "Select CSV files to delete",
            [p.name for p in csv_files],
        )
        confirm_files_delete = st.checkbox(
            "Confirm deletion of the selected CSV files."
        )

        if st.button(
            "Delete Selected Files",
            disabled=not selected_files or not confirm_files_delete,
        ):
            for filename in selected_files:
                target = (CSV_DIR / filename).resolve()
                if target.parent == CSV_DIR.resolve() and target.exists():
                    target.unlink()

            sync_uploaded_database()
            st.success("Selected files deleted.")
            st.rerun()
    else:
        st.info("No CSV files uploaded yet.")

# -------------------- Explore Data --------------------

elif page == "Explore Data":
    st.title("Explore Data")

    database_name = st.selectbox(
        "Choose database",
        ["Sample database", "Uploaded CSV database"],
    )
    tables = get_tables(database_name)

    if not tables:
        st.info("No tables found. Upload a CSV in Dataset Manager.")
    else:
        table_name = st.selectbox("Choose table", tables)
        conn = connect_for_database(database_name)

        try:
            safe_table = table_name.replace('"', '""')
            preview = pd.read_sql_query(
                f'SELECT * FROM "{safe_table}" LIMIT 1000',
                conn,
            )
            st.subheader(f"Preview: {table_name}")
            st.dataframe(preview, use_container_width=True)

            st.subheader("Column Information")
            schema = pd.read_sql_query(
                f'PRAGMA table_info("{safe_table}")',
                conn,
            )
            st.dataframe(schema, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("Preview Rows", len(preview))
            col2.metric("Columns", len(preview.columns))

        except Exception as exc:
            st.error(f"Could not inspect table: {exc}")
        finally:
            conn.close()

# -------------------- Progress & Notes --------------------

elif page == "Progress & Notes":
    st.title("Progress & Notes")

    if not st.session_state.logged_in:
        st.warning(
            "Sign in through Question Management to save and view "
            "your personal progress and notes."
        )
        st.info(
            "The current authentication is an administrator login. "
            "It does not create separate learner accounts."
        )
    else:
        username = st.session_state.username
        questions = load_questions()
        completed = get_completed_ids(username)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Questions", len(questions))
        col2.metric("Completed", len(completed))
        col3.metric(
            "Completion",
            f"{100 * len(completed) / len(questions):.1f}%"
            if questions else "0%",
        )

        progress_rows = []
        for q in questions:
            progress_rows.append({
                "ID": q["id"],
                "Level": q["level"],
                "Question": q["title"],
                "Completed": "Yes" if q["id"] in completed else "No",
                "Topic": q["topic"],
            })

        if progress_rows:
            st.dataframe(
                pd.DataFrame(progress_rows),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Use the Practice Lab to run a query and save notes for "
            "individual questions."
        )

# -------------------- About --------------------

elif page == "About":
    st.title("About SQL Interview Lab")

    st.markdown("""
    **SQL Interview Lab** is a Streamlit-based SQL learning and
    interview-practice application.

    ### Features
    - Basic, Intermediate, and Expert SQL questions
    - SQL query editor with read-only query execution
    - Hints, solutions, and explanations
    - SQLite sample database
    - CSV upload and exploration
    - Persistent question bank
    - Administrator login and question management
    - Contributor attribution
    - Progress tracking and personal notes

    ### Technologies
    Python · Streamlit · SQLite · Pandas · SQL
    """)

    st.caption(
        "For production deployment, configure a secure administrator "
        "provisioning process and protect the application with "
        "appropriate server-side access controls."
    )

# -------------------- Footer --------------------

st.sidebar.divider()
st.sidebar.caption("SQL Interview Lab · Python + Streamlit + SQLite")
