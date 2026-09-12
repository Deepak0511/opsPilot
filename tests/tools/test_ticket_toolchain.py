import pytest
from datetime import date
from ops_pilot.tools.ticket_toolchain import (
    search_ticket_by_id_tool,
    search_tickets_tool,
    create_ticket_tool,
    update_ticket_tool,
    string_to_date,
)
from ops_pilot.models.ticket import Ticket
from ops_pilot.models.employee import Employee
from ops_pilot.models.system import System

@pytest.fixture
def mock_ticket():
    return Ticket(
        id="INC-001",
        employee_id="E001",
        title="Laptop broken",
        description="Screen cracked",
        status="Open",
        priority="High",
        category="Hardware",
        system_id="SYS-001",
        assigned_to="A001",
        created_date=date(2023, 10, 27),
        updated_date=date(2023, 10, 27),
        notes="None"
    )

def test_search_ticket_by_id_tool(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.find_ticket_by_id", return_value=mock_ticket)
    result = search_ticket_by_id_tool.invoke({"ticket_id": "INC-001"})
    assert result.id == "INC-001"

def test_search_ticket_by_id_tool_not_found(mocker):
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.find_ticket_by_id", return_value=None)
    with pytest.raises(ValueError, match="does not exist"):
        search_ticket_by_id_tool.invoke({"ticket_id": "INC-999"})

def test_search_tickets_tool(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.search_tickets", return_value=[mock_ticket])
    result = search_tickets_tool.invoke({"employee_id": "E001", "category": "Hardware"})
    assert len(result) == 1
    assert result[0].id == "INC-001"

def test_search_tickets_tool_no_args():
    with pytest.raises(ValueError, match="At least one search parameter besides employee_id"):
        search_tickets_tool.invoke({"employee_id": "E001"})

def test_create_ticket_tool(mocker, mock_ticket):
    # Mock employee and system verification
    mocker.patch("ops_pilot.tools.ticket_toolchain.employee_repository.find_employee_by_id", return_value=Employee(id="E001", name="Test", email="test@test", department="IT"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.system_repository.find_system_by_id", return_value=System(id="SYS-001", name="Test System", status="Online"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.ulid.new", return_value="ULID-123")
    
    # Mock create
    mock_create = mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.create_ticket")
    mock_create.return_value = mock_ticket
    
    result = create_ticket_tool.invoke({
        "employee_id": "E001",
        "title": "Test",
        "description": "Test Desc",
        "status": "Open",
        "priority": "Low",
        "category": "Software",
        "system_id": "SYS-001",
        "assigned_to": "A001",
        "notes": ""
    })
    
    assert result.id == "INC-001"
    mock_create.assert_called_once()

def test_update_ticket_tool(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.find_ticket_by_id", return_value=mock_ticket)
    mock_update = mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.update_ticket")
    mock_update.return_value = mock_ticket
    
    result = update_ticket_tool.invoke({
        "ticket_id": "INC-001",
        "status": "Closed"
    })
    
    assert result.status == "Closed"
    mock_update.assert_called_once()

def test_string_to_date():
    assert string_to_date(None) is None
    d = string_to_date("2023-10-27")
    assert d == date(2023, 10, 27)
