import os

# Set DB_PATH globally BEFORE any application code is imported
# This ensures all module-level DB_PATH variables resolve to the test database natively.
_test_db = os.path.join(os.getcwd(), "test_db.sqlite")
os.environ["DB_PATH"] = _test_db
if os.path.exists(_test_db):
    os.remove(_test_db)

import sqlite3
import tempfile
import pytest

from ops_pilot.config.settings import lookup_for_setting

@pytest.fixture(scope="session")
def temp_db_path():
    path = os.path.join(os.getcwd(), "test_db.sqlite")
    # Remove if exists from previous run
    if os.path.exists(path):
        os.remove(path)
    
    # Initialize the schema
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create Employees Table
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
    
    # Create Tickets Table
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
    
    # Create Knowledge Base Table
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
    
    # Create Systems Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS systems (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            last_checked TEXT
        )
    """)
    
    # id_sequences is created dynamically by id_generator, but we can pre-create it
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS id_sequences (
            prefix TEXT PRIMARY KEY,
            next_val INTEGER NOT NULL DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup after tests
    try:
        os.remove(path)
    except OSError:
        pass

@pytest.fixture(autouse=True)
def clean_db(temp_db_path):
    """Clear all tables before each test to prevent data collision (IntegrityError)."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees")
    cursor.execute("DELETE FROM tickets")
    cursor.execute("DELETE FROM knowledge_base")
    cursor.execute("DELETE FROM systems")
    cursor.execute("DELETE FROM id_sequences")
    conn.commit()
    conn.close()

@pytest.fixture
def db_connection(temp_db_path):
    """Provide a direct DB connection for tests to arrange/assert data."""
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
