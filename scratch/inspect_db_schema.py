import sqlite3
from pathlib import Path

db_path = Path("c:/RSE Time/chatbot/data/chatbot_history.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:", tables)

# Get schema of each table
for table in tables:
    cursor.execute(f"PRAGMA table_info({table});")
    info = cursor.fetchall()
    print(f"\nTable: {table}")
    for col in info:
        print(f"  Column: {col[1]} ({col[2]})")

conn.close()
