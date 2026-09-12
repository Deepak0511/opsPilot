# Data access layer
import sqlite3
from typing import Optional
from ops_pilot.config.settings import lookup_for_setting
from ops_pilot.models.knowledge_base import KnowledgeBase

DB_PATH = lookup_for_setting["env_db_path"]

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row    # Return dicts, not tuples
    return conn

def find_knowledge_base_by_id(kb_id: str) -> Optional[KnowledgeBase]:
    """ fetches knowledge base article by id and returns a KnowledgeBase object if found, else returns None """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_base WHERE id = ?", (kb_id,))
        row = cursor.fetchone()
        if row:
            return KnowledgeBase.model_validate(dict(row))  # sqlite3.Row → dict → Pydantic
        return None
    finally:
        conn.close()

# Tries to find KB articles by title.
def search_knowledge_base_by_title(title: str) -> list[KnowledgeBase]:
    """Returns a list of KnowledgeBase objects whose titles contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_base WHERE LOWER(title) LIKE ?",
            (f"%{title.lower()}%",)
        )
        rows = cursor.fetchall()
        return [KnowledgeBase.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

def search_knowledge_base_by_category(category: str) -> list[KnowledgeBase]:
    """Returns a list of KnowledgeBase objects whose categories contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_base WHERE LOWER(category) LIKE ?",
            (f"%{category.lower()}%",)
        )
        rows = cursor.fetchall()
        return [KnowledgeBase.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()


def search_knowledge_base_by_tag(tag: str) -> list[KnowledgeBase]:
    """Returns a list of KnowledgeBase objects whose tags contain the given substring (case-insensitive)"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_base WHERE LOWER(tags) LIKE ?",
            (f"%{tag.lower()}%",)
        )
        rows = cursor.fetchall()
        return [KnowledgeBase.model_validate(dict(row)) for row in rows]
    finally:
        conn.close()

# We need to create a KB Article if any new kind of issue is found.
def create_knowledge_base(kb: KnowledgeBase) -> KnowledgeBase:
    """Persists a new knowledge base article in the database and returns the created KnowledgeBase object"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO knowledge_base (id, title, category, content, Incident_id, tags)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (kb.id, kb.title, kb.category, kb.content, kb.Incident_id, ','.join(kb.tags))
        )
        conn.commit()
        return kb
    finally:
        conn.close()

def update_knowledge_base(kb: KnowledgeBase) -> KnowledgeBase:
    """ fetches knowledge base article by id and updates it, returning the updated KnowledgeBase object """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE knowledge_base
               SET title = ?, category = ?, content = ?, Incident_id = ?, tags = ?
               WHERE id = ?""",
            (kb.title, kb.category, kb.content, kb.Incident_id, ','.join(kb.tags), kb.id)
        )
        conn.commit()
        return kb
    finally:
        conn.close()

def delete_knowledge_base(kb_id: str) -> None:
    """ fetches knowledge base article by id and deletes it """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_base WHERE id = ?", (kb_id,))
        conn.commit()
    finally:
        conn.close()

def count_knowledge_base_articles(title: Optional[str] = None, category: Optional[str] = None,
                                   incident_id: Optional[str] = None, tag: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM knowledge_base WHERE 1=1"
        params = []
        if title:
            query += " AND LOWER(title) LIKE ?"
            params.append(f"%{title.lower()}%")
        if category:
            query += " AND LOWER(category) LIKE ?"
            params.append(f"%{category.lower()}%")
        if incident_id:
            query += " AND Incident_id = ?"
            params.append(incident_id)
        if tag:
            query += " AND LOWER(tags) LIKE ?"
            params.append(f"%{tag.lower()}%")
        cursor.execute(query, tuple(params))
        return cursor.fetchone()[0]
    finally:
        conn.close()
