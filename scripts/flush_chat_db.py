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

def flush_chat_db():
    db_path = lookup_for_setting["env_checkpoint_db_path"]
    print(f"Flushing chat database at {db_path}...")
    
    if not os.path.exists(db_path):
        print("Chat database file does not exist. Nothing to flush.")
        return

    # Delete the database file entirely to flush it
    try:
        os.remove(db_path)
        print("Successfully removed chat database file.")
    except Exception as e:
        print(f"Error removing database file: {e}")
        print("Attempting to connect and drop tables instead...")
        # Fallback: Drop LangGraph checkpointer tables if locked
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table_name in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]}")
            conn.commit()
            conn.close()
            print("Successfully dropped all tables in chat database.")
        except Exception as ex:
            print(f"Failed to drop tables: {ex}")

if __name__ == "__main__":
    flush_chat_db()
