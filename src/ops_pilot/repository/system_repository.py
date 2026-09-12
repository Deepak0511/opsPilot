# Data access layer
import sqlite3
from typing import Optional
from ops_pilot.config.settings import lookup_for_setting
from ops_pilot.models.system import System

DB_PATH = lookup_for_setting["env_db_path"]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # Return dicts, not tuples
    return conn

def find_system_by_id(system_id: str) -> Optional[System]:
    """ fetches system by id and returns a System object if found, else returns None """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM systems WHERE id = ?", (system_id,))
        row = cursor.fetchone()
        if row:
            return System.model_validate(dict(row))  # sqlite3.Row → dict → Pydantic
        return None
    finally:
        conn.close()

def search_systems_by_name(name: str) -> list[System]:
    """Returns a list of System objects whose names contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM systems WHERE LOWER(name) LIKE ?",
            (f"%{name.lower()}%",)
        )
        rows = cursor.fetchall()
        return [System.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def search_systems_by_status(status: str) -> list[System]:
    """Returns a list of System objects whose statuses contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM systems WHERE LOWER(status) LIKE ?",
            (f"%{status.lower()}%",)
        )
        rows = cursor.fetchall()
        return [System.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def create_system(system: System) -> System:
    """Persists a new system in the database and returns the created System object"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO systems (id, name, status, description, last_checked)
               VALUES (?, ?, ?, ?, ?)""",
            (system.id, system.name, system.status, system.description, system.last_checked)
        )
        conn.commit()
        return system
    finally:
        conn.close()

def update_system(system: System) -> System:
    """Updates an existing system in the database and returns the updated System object"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE systems
               SET name = ?, status = ?, description = ?, last_checked = ?
               WHERE id = ?""",
            (system.name, system.status, system.description, system.last_checked, system.id)
        )
        conn.commit()
        return system
    finally:
        conn.close()

def delete_system(system_id: str) -> None:
    """Deletes a system from the database by its ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM systems WHERE id = ?", (system_id,))
        conn.commit()
    finally:
        conn.close()

def count_systems(name: Optional[str] = None, status: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM systems WHERE 1=1"
        params = []
        if name:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{name.lower()}%")
        if status:
            query += " AND LOWER(status) LIKE ?"
            params.append(f"%{status.lower()}%")
        cursor.execute(query, tuple(params))
        return cursor.fetchone()[0]
    finally:
        conn.close()
