import sqlite3
import uuid
import os
import re
from passlib.hash import bcrypt

def verify_password(password, hashed):
    try:
        if bcrypt.verify(password, hashed):
            return True
        # If verify raises ValueError (invalid hash), fall back to exact match below
    except Exception:
        pass
    return password == hashed
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            FOREIGN KEY(email) REFERENCES users(email)
        )
    ''')
    # Create org tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            org_name TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            country TEXT,
            bio TEXT,
            number_of_employees INTEGER,
            ceo TEXT,
            goals TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_sessions (
            token TEXT PRIMARY KEY,
            org_name TEXT NOT NULL,
            FOREIGN KEY(org_name) REFERENCES organizations(org_name)
        )
    ''')
    # Create organizational financial data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            date TEXT,
            industry TEXT,
            stage TEXT,
            goal TEXT,
            revenue REAL,
            fixed_cost REAL,
            variable_cost REAL,
            total_cost REAL,
            profit REAL,
            cash_reserve REAL,
            debt REAL,
            growth_rate REAL,
            customer_count INTEGER,
            cac REAL,
            ltv REAL,
            profit_margin REAL,
            burn_rate REAL,
            runway_months REAL,
            debt_ratio REAL,
            risk_level TEXT,
            health_score REAL,
            recommendation TEXT,
            FOREIGN KEY(org_name) REFERENCES organizations(org_name)
        )
    ''')
    conn.commit()
    conn.close()
# Initialize upon import
init_db()

def signup(name, email, password):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone() is not None:
        conn.close()
        return {"success": False, "error": "Email already exists"}
    
    hashed_pw = bcrypt.hash(password)
    cursor.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", (email, name, hashed_pw))
    
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "name": name}

def login(identifier, password):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE OR name = ? COLLATE NOCASE", (identifier, identifier))
    user = cursor.fetchone()
    
    if user is None:
        conn.close()
        return {"success": False, "error": "Invalid email or username"}
    
    if not verify_password(password, user["password"]):
        conn.close()
        return {"success": False, "error": "Invalid password"}
        
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, user["email"]))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "name": user["name"], "email": user["email"]}

def get_user_from_token(token):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT users.email, users.name 
        FROM sessions 
        JOIN users ON sessions.email = users.email 
        WHERE sessions.token = ?
    ''', (token,))
    
    user = cursor.fetchone()
    if user:
        conn.close()
        return {"email": user["email"], "name": user["name"], "type": "individual"}
        
    cursor.execute('''
        SELECT organizations.org_name 
        FROM org_sessions 
        JOIN organizations ON org_sessions.org_name = organizations.org_name 
        WHERE org_sessions.token = ?
    ''', (token,))
    
    org = cursor.fetchone()
    conn.close()
    
    if org:
        return {"org_name": org["org_name"], "type": "organization"}
        
    return None

def logout(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    cursor.execute("DELETE FROM org_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return {"success": True}

def org_signup(org_name, password, country=None, bio=None, number_of_employees=None, ceo=None, goals=None):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM organizations WHERE org_name = ?", (org_name,))
    if cursor.fetchone() is not None:
        conn.close()
        return {"success": False, "error": "Organization name already exists"}
    
    hashed_pw = bcrypt.hash(password)
    cursor.execute('''
        INSERT INTO organizations 
        (org_name, password, country, bio, number_of_employees, ceo, goals) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (org_name, hashed_pw, country, bio, number_of_employees, ceo, goals))
    
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO org_sessions (token, org_name) VALUES (?, ?)", (token, org_name))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "org_name": org_name}

def org_login(org_name, password):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM organizations WHERE org_name = ? COLLATE NOCASE", (org_name,))
    org = cursor.fetchone()
    
    if org is None:
        conn.close()
        return {"success": False, "error": "Invalid organization name"}
    
    if not verify_password(password, org["password"]):
        conn.close()
        return {"success": False, "error": "Invalid password"}
        
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO org_sessions (token, org_name) VALUES (?, ?)", (token, org["org_name"]))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "org_name": org["org_name"]}

def update_security(email, current_password, new_email=None, new_password=None):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {"success": False, "error": "User not found"}
        
    if not verify_password(current_password, user["password"]):
        conn.close()
        return {"success": False, "error": "Incorrect current password"}

    if new_email and new_email != email:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            conn.close()
            return {"success": False, "error": "Invalid email format"}
        cursor.execute("SELECT * FROM users WHERE email = ?", (new_email,))
        if cursor.fetchone() is not None:
            conn.close()
            return {"success": False, "error": "Email already in use"}
            
        # Due to foreign key constraint without CASCADE, update sessions first then users
        cursor.execute("UPDATE sessions SET email = ? WHERE email = ?", (new_email, email))
        cursor.execute("UPDATE users SET email = ? WHERE email = ?", (new_email, email))
        email = new_email
        
    if new_password:
        if len(new_password) < 6:
            conn.close()
            return {"success": False, "error": "Password must be at least 6 characters"}
        hashed_pw = bcrypt.hash(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
        
    conn.commit()
    conn.close()
    return {"success": True, "message": "Security settings updated successfully"}

# --- NEW: Org Data Helpers ---

def add_org_data_rows(org_name, rows):
    """Expects a list of dicts with keys matching org_financial_data columns."""
    conn = get_db()
    cursor = conn.cursor()
    
    # First, clear existing data for this org (as per replacement policy)
    cursor.execute("DELETE FROM org_financial_data WHERE org_name = ?", (org_name,))
    
    cols = [
        "org_name", "date", "industry", "stage", "goal", "revenue", 
        "fixed_cost", "variable_cost", "total_cost", "profit", 
        "cash_reserve", "debt", "growth_rate", "customer_count", 
        "cac", "ltv", "profit_margin", "burn_rate", "runway_months", 
        "debt_ratio", "risk_level", "health_score", "recommendation"
    ]
    
    query = f"INSERT INTO org_financial_data ({', '.join(cols)}) VALUES ({', '.join(['?' for _ in cols])})"
    
    for row in rows:
        vals = [org_name] + [row.get(c) for c in cols[1:]]
        cursor.execute(query, vals)
        
    conn.commit()
    conn.close()
    return True

def get_org_data_rows_from_db(org_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM org_financial_data WHERE org_name = ?", (org_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
