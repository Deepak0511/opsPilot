import os
import sys
from pathlib import Path
import sqlite3

# Add project root and src to path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ops_pilot.config.settings import lookup_for_setting

def flush_ops_db():
    db_path = lookup_for_setting["env_db_path"]
    print(f"Flushing ops database at {db_path}...")
    
    if not os.path.exists(db_path):
        print("Database file does not exist. Nothing to flush.")
        return

    # Delete the database file entirely to flush it
    try:
        os.remove(db_path)
        print("Successfully removed ops database file.")
    except Exception as e:
        print(f"Error removing database file: {e}")
        print("Attempting to connect and delete all records instead...")
        # Fallback: Delete records if file is locked
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            tables = ["employees", "tickets", "knowledge_base", "systems", "id_sequences"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()
            conn.close()
            print("Successfully truncated all tables in ops database.")
        except Exception as ex:
            print(f"Failed to truncate tables: {ex}")

if __name__ == "__main__":
    flush_ops_db()
