# Data access layer
import sqlite3
from typing import Optional
from ops_pilot.config.settings import lookup_for_setting
from ops_pilot.models.ticket import Ticket
from ops_pilot.utils.logger import log

DB_PATH = lookup_for_setting["env_db_path"] 

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # Return dicts, not tuples
    return conn


def find_ticket_by_id(ticket_id: str) -> Optional[Ticket]:
    """ fetches ticket by id and returns a Ticket object if found, else returns None """
    log.debug(f"Executing find_ticket_by_id for ticket_id='{ticket_id}'")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row:
            return Ticket.model_validate(dict(row))  # sqlite3.Row → dict → Pydantic
        return None
    finally:
        conn.close()

def search_tickets_by_title(title: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose titles contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE LOWER(title) LIKE ?",
            (f"%{title.lower()}%",)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

# This one will be helpful for the admin dashboard.
def search_tickets_by_status(status: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose statuses contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE status = ?",
            (status,)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def search_tickets_by_priority(priority: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose priorities contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE priority = ?",
            (priority,)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def search_tickets_by_category(category: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose categories contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE category = ?",
            (category,)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()


def search_tickets_by_employee_id(employee_id: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose employee_id matches the given employee_id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE employee_id = ?",
            (employee_id,)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()


def search_tickets_by_date_range(start_date: str, end_date: str) -> list[Ticket]:
    """Returns a list of Ticket objects whose created_date falls within the given date range"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE created_date BETWEEN ? AND ?",
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def search_tickets_by_system_id(system_id: str) -> list[Ticket]: 
    """Returns a list of Ticket objects whose system_id matches the given system_id"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tickets WHERE system_id = ?",
            (system_id,)
        )
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

# Mega Function to search tickets by multiple criteria. This will be useful in chats where a user has only rough idea of thier issue.
def search_tickets(title: Optional[str] = None, description: Optional[str] = None, 
                   category: Optional[str] = None, employee_id: Optional[str] = None, 
                   system_id: Optional[str] = None, assigned_to: Optional[str] = None,
                   start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[Ticket]:
    """Returns a list of Ticket objects based on multiple search criteria"""
    log.debug(f"Executing search_tickets with filters: title={title}, category={category}, employee={employee_id}")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []

        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        if description:
            query += " AND description LIKE ?"
            params.append(f"%{description}%")
        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")
        if employee_id:
            query += " AND employee_id = ?"
            params.append(employee_id)
        if system_id:
            query += " AND system_id = ?"
            params.append(system_id)
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)    
        if start_date and end_date:
            query += " AND created_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [Ticket.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

# Below goes modification functions

def create_ticket(ticket: Ticket) -> Ticket:
    """Persists a new ticket in the database and returns the created Ticket object"""
    log.debug(f"Executing create_ticket for ticket_id='{ticket.id}'")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tickets (id, employee_id, title, description, 
                status, priority, category, system_id, assigned_to, created_date, updated_date, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticket.id, ticket.employee_id, ticket.title, ticket.description, 
             ticket.status, ticket.priority, ticket.category, ticket.system_id, 
             ticket.assigned_to, ticket.created_date, ticket.updated_date, ticket.notes)
        )
        conn.commit()
        return ticket
    finally:
        conn.close()

def update_ticket(ticket: Ticket) -> Ticket:
    """Updates an existing ticket in the database and returns the updated Ticket object"""
    log.debug(f"Executing update_ticket for ticket_id='{ticket.id}'")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE tickets
               SET employee_id = ?, title = ?, description = ?, 
                   status = ?, priority = ?, category = ?, system_id = ?, 
                   assigned_to = ?, created_date = ?, updated_date = ?, notes = ?
               WHERE id = ?""",
            (ticket.employee_id, ticket.title, ticket.description, 
             ticket.status, ticket.priority, ticket.category, ticket.system_id, 
             ticket.assigned_to, ticket.created_date, ticket.updated_date, ticket.notes,
             ticket.id)
        )
        conn.commit()
        return ticket
    finally:
        conn.close()


def delete_ticket(ticket_id: str) -> None:
    """Deletes a ticket from the database by its ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        conn.commit()
    finally:
        conn.close()