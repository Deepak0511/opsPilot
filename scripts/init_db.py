import sqlite3
import os
import sys
from pathlib import Path

# Add project root and src to path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ops_pilot.config.settings import lookup_for_setting

DB_PATH = lookup_for_setting["env_db_path"]

def init_db():
    print(f"Initializing database at {DB_PATH}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT,
            device_type TEXT,
            device_id TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            category TEXT NOT NULL,
            system_id TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            created_date DATE NOT NULL,
            updated_date DATE NOT NULL,
            notes TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            Incident_id TEXT,
            tags TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS systems (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            last_checked TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS id_sequences (
            prefix TEXT PRIMARY KEY,
            next_val INTEGER NOT NULL DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("Database initialization complete! Schema created.")

if __name__ == "__main__":
    init_db()
