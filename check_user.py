import sqlite3
import os

db_path = "/home/lex/lexmakesit/backend/sql_app.db"
if not os.path.exists(db_path):
    print(f"File {db_path} does not exist.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)

    cursor.execute("SELECT * FROM users WHERE email='thegamermasterninja@gmail.com';")
    user = cursor.fetchone()
    if user:
        print("User found:", user)
        # Assuming column names based on model: id, email, password_hash, full_name, is_active, is_verified, created_at, last_login_at
    else:
        print("User not found.")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
