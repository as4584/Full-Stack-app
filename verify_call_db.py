import sqlite3
import json
import os

db_path = 'backend/sql_app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get the most recent call
    cursor.execute("""
        SELECT id, call_sid, from_number, status, duration, appointment_booked, intent, transcript, created_at, updated_at 
        FROM calls 
        ORDER BY created_at DESC 
        LIMIT 1;
    """)
    row = cursor.fetchone()
    if row:
        print("Last Call in DB:")
        cols = ["id", "call_sid", "from_number", "status", "duration", "appointment_booked", "intent", "transcript", "created_at", "updated_at"]
        data = dict(zip(cols, row))
        for k, v in data.items():
            if k == 'transcript' and v:
                print(f"{k}: {v[:100]}...")
            else:
                print(f"{k}: {v}")
    else:
        print("No calls found in DB.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
