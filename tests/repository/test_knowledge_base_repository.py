import pytest
from ops_pilot.repository.knowledge_base_repository import (
    create_knowledge_base,
    find_knowledge_base_by_id,
    search_knowledge_base_by_title,
    search_knowledge_base_by_category,
    search_knowledge_base_by_tag,
    update_knowledge_base,
    delete_knowledge_base,
    count_knowledge_base_articles,
)
from ops_pilot.models.knowledge_base import KnowledgeBase

@pytest.fixture
def sample_kb():
    return KnowledgeBase(
        id="KB-001",
        title="How to reset password",
        category="Authentication",
        content="Follow these steps to reset your password...",
        Incident_id=None,
        tags=["password", "reset", "auth"]
    )

def test_create_and_find_kb_by_id(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    found = find_knowledge_base_by_id(sample_kb.id)
    assert found is not None
    assert found.title == sample_kb.title
    # Note: Pydantic parses the comma separated string "password,reset,auth" into a list if properly configured,
    # or the model validate handles it. We'll just verify the title for now.
    
def test_search_kb_by_title(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    results = search_knowledge_base_by_title("reset password")
    assert len(results) == 1
    assert results[0].id == sample_kb.id
    
    results = search_knowledge_base_by_title("vpn")
    assert len(results) == 0


def test_search_kb_by_natural_language_terms(db_connection):
    article = KnowledgeBase(
        id="KB-002",
        title="Guest WiFi Access",
        category="Network",
        content="Guests can connect to the office guest network.",
        Incident_id=None,
        tags=["wifi", "network"],
    )
    create_knowledge_base(article)

    results = search_knowledge_base_by_title("How do I connect to wifi?")

    assert [result.id for result in results] == ["KB-002"]

def test_search_kb_by_category(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    results = search_knowledge_base_by_category("auth")
    assert len(results) == 1
    
    results = search_knowledge_base_by_category("network")
    assert len(results) == 0

def test_search_kb_by_tag(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    results = search_knowledge_base_by_tag("password")
    assert len(results) == 1

def test_update_kb(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    sample_kb.title = "How to securely reset password"
    update_knowledge_base(sample_kb)
    
    found = find_knowledge_base_by_id(sample_kb.id)
    assert found.title == "How to securely reset password"

def test_delete_kb(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    delete_knowledge_base(sample_kb.id)
    
    found = find_knowledge_base_by_id(sample_kb.id)
    assert found is None

def test_count_kb_articles(db_connection, sample_kb):
    create_knowledge_base(sample_kb)
    
    assert count_knowledge_base_articles() == 1
    assert count_knowledge_base_articles(title="reset") == 1
    assert count_knowledge_base_articles(category="auth") == 1
    assert count_knowledge_base_articles(category="network") == 0
