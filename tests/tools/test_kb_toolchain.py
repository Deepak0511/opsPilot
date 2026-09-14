import pytest
from ops_pilot.tools.kb_toolchain import (
    count_knowledge_base_articles_tool,
    search_knowledge_base_tool,
)
from ops_pilot.models.knowledge_base import KnowledgeBase

@pytest.fixture
def mock_kb():
    return KnowledgeBase(
        id="KB-001",
        title="Reset Password",
        category="Auth",
        content="Steps to reset.",
        Incident_id="INC-001",
        tags=["password"]
    )

def test_count_knowledge_base_articles_tool(mocker):
    mock_count = mocker.patch("ops_pilot.tools.kb_toolchain.kb_repository.count_knowledge_base_articles")
    mock_count.return_value = 2
    
    result = count_knowledge_base_articles_tool.invoke({"title": "Reset"})
    assert result == 2
    mock_count.assert_called_once_with(title="Reset", category=None, incident_id=None, tag=None)

def test_search_knowledge_base_tool_no_args():
    result = search_knowledge_base_tool.invoke({})
    assert isinstance(result, str) and result.startswith("Validation Error")

def test_search_knowledge_base_tool_by_title(mocker, mock_kb):
    mock_search = mocker.patch("ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_title")
    mock_search.return_value = [mock_kb]
    
    results = search_knowledge_base_tool.invoke({"title": "Reset"})
    assert len(results) == 1
    assert results[0].id == "KB-001"
    mock_search.assert_called_once_with("Reset")

def test_search_knowledge_base_tool_multiple_filters(mocker, mock_kb):
    mock_search_title = mocker.patch("ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_title")
    mock_search_title.return_value = [mock_kb]
    
    mock_search_category = mocker.patch("ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_category")
    mock_search_category.return_value = [mock_kb]
    
    results = search_knowledge_base_tool.invoke({"title": "Reset", "category": "Auth"})
    assert len(results) == 1
    
def test_search_knowledge_base_tool_not_found(mocker):
    mocker.patch("ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_title", return_value=[])

    result = search_knowledge_base_tool.invoke({"title": "Unknown"})
    assert isinstance(result, str) and result.startswith("Validation Error")
