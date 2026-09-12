"""
ID Generation Utility for OpsPilot.

Generates human-readable, pattern-based unique identifiers.

Patterns
--------
Employee : 6-char alphanumeric (human-friendly)   e.g. A3K9M2
Ticket   : <TYPE>-<serial>                        e.g. INC-001, RIT-042
KB       : KB-<serial>                             e.g. KB-001, KB-017
System   : Use ulid.new() directly (ulid-py)
"""

import random
import sqlite3


# Human-friendly charset — no 0/O, 1/I/l confusion
_FRIENDLY_CHARS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

# Valid ticket type prefixes
TICKET_TYPE_INCIDENT = "INC"
TICKET_TYPE_REQUEST = "RIT"
VALID_TICKET_TYPES = {TICKET_TYPE_INCIDENT, TICKET_TYPE_REQUEST}


# ---------------------------------------------------------------------------
# Sequence Table (auto-created on first use)
# ---------------------------------------------------------------------------

def _next_serial(conn: sqlite3.Connection, prefix: str) -> int:
    """
    Atomically get-and-increment a serial number for the given prefix.

    Uses SQLite's UPSERT (INSERT ... ON CONFLICT ... DO UPDATE) so:
      - First call for a prefix → inserts row with next_val=1, returns 1
      - Subsequent calls       → increments next_val, returns new value

    The id_sequences table is auto-created if it doesn't exist.

    Java analogy: like Oracle's CREATE SEQUENCE + NEXTVAL, but simpler.

    Parameters
    ----------
    conn : sqlite3.Connection
        Active database connection.
    prefix : str
        The sequence name / ID prefix (e.g. "INC", "RIT", "KB").

    Returns
    -------
    int
        The next serial number.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS id_sequences (
            prefix   TEXT PRIMARY KEY,
            next_val INTEGER NOT NULL DEFAULT 1
        )
    """)
    cursor = conn.execute(
        """
        INSERT INTO id_sequences (prefix, next_val) VALUES (?, 1)
        ON CONFLICT(prefix) DO UPDATE SET next_val = next_val + 1
        RETURNING next_val
        """,
        (prefix,),
    )
    serial = cursor.fetchone()[0]
    conn.commit()
    return serial


# ---------------------------------------------------------------------------
# Employee ID — 6-char alphanumeric, no DB needed
# ---------------------------------------------------------------------------

def generate_employee_id(length: int = 6) -> str:
    """
    Generate a random, human-readable employee ID.

    Uses an unambiguous charset (no 0/O, 1/I confusion).

    Returns
    -------
    str
        e.g. "A3K9M2", "R7PN4X"
    """
    return "".join(random.choices(_FRIENDLY_CHARS, k=length))


# ---------------------------------------------------------------------------
# Ticket ID — <TYPE>-<serial>
# ---------------------------------------------------------------------------

def generate_ticket_id(conn: sqlite3.Connection, ticket_type: str = "INC") -> str:
    """
    Generate the next ticket ID: INC-001, RIT-042, etc.

    Queries SQLite for the next serial number automatically.

    Parameters
    ----------
    conn : sqlite3.Connection
        Active database connection.
    ticket_type : str
        "INC" (incident) or "RIT" (request). Default "INC".

    Returns
    -------
    str
        e.g. "INC-001", "RIT-003"

    Raises
    ------
    ValueError
        If ticket_type is invalid.
    """
    if ticket_type not in VALID_TICKET_TYPES:
        raise ValueError(
            f"Invalid ticket type '{ticket_type}'. "
            f"Must be one of: {VALID_TICKET_TYPES}"
        )
    serial = _next_serial(conn, ticket_type)
    return f"{ticket_type}-{serial:03d}"


# ---------------------------------------------------------------------------
# Knowledge Base Article ID — KB-<serial>
# ---------------------------------------------------------------------------

def generate_kb_id(conn: sqlite3.Connection) -> str:
    """
    Generate the next KB article ID: KB-001, KB-002, etc.

    Parameters
    ----------
    conn : sqlite3.Connection
        Active database connection.

    Returns
    -------
    str
        e.g. "KB-001", "KB-017"
    """
    serial = _next_serial(conn, "KB")
    return f"KB-{serial:03d}"
