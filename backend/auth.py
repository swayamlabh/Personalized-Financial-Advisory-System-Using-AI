import sqlite3
import uuid
import os

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
    
    cursor.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", (email, name, password))
    
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "name": name}

def login(email, password):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if user is None:
        conn.close()
        return {"success": False, "error": "Invalid email"}
    
    if user["password"] != password:
        conn.close()
        return {"success": False, "error": "Invalid password"}
        
    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "token": token, "name": user["name"]}

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
    conn.close()
    
    if not user:
        return None
    return {"email": user["email"], "name": user["name"]}

def logout(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return {"success": True}
