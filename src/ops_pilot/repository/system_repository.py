# Data access layer
import sqlite3
import re
from typing import Optional
from ops_pilot.config.settings import lookup_for_setting
from ops_pilot.models.system import System
from ops_pilot.utils.logger import log

DB_PATH = lookup_for_setting["env_db_path"]

_SYSTEM_STOP_WORDS = {
    "a", "an", "and", "are", "available", "can", "configure", "configuration",
    "do", "for", "from", "help", "how", "i", "is", "it", "me", "my", "of",
    "please", "problem", "public", "request", "service", "status", "system",
    "the", "this", "to", "up", "what", "why", "with", "you",
    "unable", "cannot", "cant", "connect", "access", "working", "broken",
    "issue", "error", "need", "want", "fix", "getting", "not", "am", "im"
}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # Return dicts, not tuples
    return conn


def _meaningful_system_terms(value: str) -> list[str]:
    """Return normalized terms useful for matching the bounded system catalog."""
    return [
        term
        for term in re.findall(r"[a-z0-9]+", value.lower())
        if term not in _SYSTEM_STOP_WORDS and len(term) > 1
    ]

def find_system_by_id(system_id: str) -> Optional[System]:
    """ fetches system by id and returns a System object if found, else returns None """
    log.debug(f"Executing find_system_by_id for system_id='{system_id}'")
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

def search_systems_by_keyword(keyword: str) -> list[System]:
    """Searches system names and descriptions using meaningful query terms."""
    log.debug(f"Executing search_systems_by_keyword for query '{keyword}'")
    terms = _meaningful_system_terms(keyword)
    if not terms:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM systems WHERE 1=1"
        params = []
        for term in terms:
            query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
            params.extend([f"%{term}%", f"%{term}%"])
            
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [System.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()


def search_supported_systems_from_request(request_text: str) -> list[System]:
    """Find the most relevant Patliputra-Corp catalog records for a full request.

    This resolver is intentionally repository-level rather than an LLM-facing tool.
    It performs an OR-style candidate search and returns only the highest-scoring
    records, allowing a request such as ``"How do I reset my VPN password?"`` to
    match a VPN record even when ``password`` is not present in its description.
    """
    terms = _meaningful_system_terms(request_text)
    if not terms:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM systems ORDER BY id ASC")
        systems = [System.model_validate(dict(row)) for row in cursor.fetchall()]
    finally:
        conn.close()

    scored: list[tuple[int, int, System]] = []
    normalized_request = " ".join(terms)
    for system in systems:
        name = system.name.lower()
        description = (system.description or "").lower()
        catalog_text = f"{name} {description}"
        matched_terms = {
            term for term in terms
            if re.search(r'\b' + re.escape(term) + r'\b', catalog_text)
        }
        if not matched_terms:
            continue

        # Prefer exact catalog-name phrases, then the number of meaningful terms.
        exact_name_match = int(
            normalized_request in name or name in normalized_request
        )
        score = len(matched_terms)
        scored.append((exact_name_match, score, system))

    if not scored:
        return []

    best_exact, best_score, _ = max(scored, key=lambda item: (item[0], item[1]))
    return [
        system
        for exact, score, system in scored
        if exact == best_exact and score == best_score
    ]

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
    log.debug(f"Executing create_system for system_id='{system.id}'")
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

def count_systems(keyword: Optional[str] = None, status: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM systems WHERE 1=1"
        params = []
        if keyword:
            terms = _meaningful_system_terms(keyword)
            # If a keyword is provided but no valid terms remain, it will match 0 systems
            if not terms:
                return 0
            for term in terms:
                query += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
                params.extend([f"%{term}%", f"%{term}%"])
        if status:
            query += " AND LOWER(status) LIKE ?"
            params.append(f"%{status.lower()}%")
        cursor.execute(query, tuple(params))
        return cursor.fetchone()[0]
    finally:
        conn.close()
