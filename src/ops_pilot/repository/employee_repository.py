# Data access layer
import sqlite3
from typing import Optional
from ops_pilot.config.settings import lookup_for_setting
from ops_pilot.models.employee import Employee


DB_PATH = lookup_for_setting["env_db_path"]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # Return dicts, not tuples
    return conn

def find_employee_by_id(employee_id: str) -> Optional[Employee]:
    """ fetches employee by id and returns an Employee object if found, else returns None """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        if row:
            return Employee.model_validate(dict(row))  # sqlite3.Row → dict → Pydantic
        return None
    finally:
        conn.close()

def search_employees_by_name(name: str) -> list[Employee]:
    """Returns a list of Employee objects whose names contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM employees WHERE LOWER(name) LIKE ?",
            (f"%{name.lower()}%",)
        )
        rows = cursor.fetchall()
        return [Employee.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

# I don't think this is required but anyway, will come back and revise. 
def create_employee(employee: Employee) -> Employee:
    """Persists a new employee in the database and returns the created Employee object"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO employees (id, name, email, department, role, device_type, device_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (employee.id, employee.name, employee.email, employee.department,
             employee.role, employee.device_type, employee.device_id)
        )
        conn.commit()
        return employee
    finally:
        conn.close()
