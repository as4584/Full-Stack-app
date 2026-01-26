import sqlite3
import os

db_path = "/home/lex/lexmakesit/backend/sql_app.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT email, full_name, is_active FROM users;")
    users = cursor.fetchall()
    print("All users:")
    for user in users:
        print(f"Email: {user[0]}, Name: {user[1]}, Active: {user[2]}")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
