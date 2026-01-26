import sqlite3
import os

db_path = 'backend/sql_app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("""
        SELECT id, call_sid, from_number, status, duration, appointment_booked, intent, created_at 
        FROM calls 
        WHERE created_at >= '2026-01-22' 
        ORDER BY created_at DESC;
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} calls from today.")
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
