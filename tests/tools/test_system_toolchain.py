import pytest
from ops_pilot.tools.system_toolchain import (
    count_systems_tool,
    search_systems_tool,
)
from ops_pilot.models.system import System

@pytest.fixture
def mock_system():
    return System(
        id="SYS-001",
        name="Main Database",
        status="Online",
        description="Primary PostgreSQL database",
        last_checked="2023-10-27T10:00:00Z"
    )

def test_count_systems_tool(mocker):
    mock_count = mocker.patch("ops_pilot.tools.system_toolchain.system_repository.count_systems")
    mock_count.return_value = 1
    
    result = count_systems_tool.invoke({"name": "Database"})
    assert result == 1
    mock_count.assert_called_once_with(name="Database", status=None)

def test_search_systems_tool_no_args():
    with pytest.raises(ValueError, match="At least one search parameter"):
        search_systems_tool.invoke({})

def test_search_systems_tool_by_name(mocker, mock_system):
    mock_search = mocker.patch("ops_pilot.tools.system_toolchain.system_repository.search_systems_by_name")
    mock_search.return_value = [mock_system]
    
    results = search_systems_tool.invoke({"name": "Main"})
    assert len(results) == 1
    assert results[0].id == "SYS-001"
    mock_search.assert_called_once_with("Main")

def test_search_systems_tool_by_status(mocker, mock_system):
    mock_search = mocker.patch("ops_pilot.tools.system_toolchain.system_repository.search_systems_by_status")
    mock_search.return_value = [mock_system]
    
    results = search_systems_tool.invoke({"status": "Online"})
    assert len(results) == 1
    mock_search.assert_called_once_with("Online")

def test_search_systems_tool_not_found(mocker):
    mocker.patch("ops_pilot.tools.system_toolchain.system_repository.search_systems_by_name", return_value=[])
    
    with pytest.raises(ValueError, match="No systems found matching the provided criteria."):
        search_systems_tool.invoke({"name": "Unknown"})
