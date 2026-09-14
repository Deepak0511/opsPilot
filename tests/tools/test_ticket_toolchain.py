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
    result = search_ticket_by_id_tool.invoke({"ticket_id": "INC-999"})
    assert isinstance(result, str) and result.startswith("Validation Error")

def test_search_tickets_tool(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.search_tickets", return_value=[mock_ticket])
    result = search_tickets_tool.invoke({"employee_id": "E001", "category": "Hardware"})
    assert len(result) == 1
    assert result[0].id == "INC-001"

def test_search_tickets_tool_no_args():
    result = search_tickets_tool.invoke({"employee_id": "E001"})
    assert isinstance(result, str) and result.startswith("Validation Error")

def test_create_ticket_tool(mocker, mock_ticket):
    # Mock employee and system verification
    mocker.patch("ops_pilot.tools.ticket_toolchain.employee_repository.find_employee_by_id", return_value=Employee(id="E001", name="Test", email="test@test", department="IT"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.system_repository.find_system_by_id", return_value=System(id="SYS-001", name="Test System", status="Online"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.get_connection")
    mocker.patch("ops_pilot.tools.ticket_toolchain.generate_ticket_id", return_value="INC-001")
    
    # Mock duplicate check
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.search_tickets", return_value=[])

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

def test_create_ticket_tool_duplicate(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.employee_repository.find_employee_by_id", return_value=Employee(id="E001", name="Test", email="test@test", department="IT"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.system_repository.find_system_by_id", return_value=System(id="SYS-001", name="Test System", status="Online"))
    
    # Mock duplicate check to return an existing Open ticket
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.search_tickets", return_value=[mock_ticket])

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
    
    assert "Duplicate Ticket Detected" in result

def test_create_ticket_tool_fallback_system(mocker, mock_ticket):
    mocker.patch("ops_pilot.tools.ticket_toolchain.employee_repository.find_employee_by_id", return_value=Employee(id="E001", name="Test", email="test@test", department="IT"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.system_repository.find_system_by_id", return_value=System(id="SYS-HW", name="Test System", status="Online"))
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.get_connection")
    mocker.patch("ops_pilot.tools.ticket_toolchain.generate_ticket_id", return_value="INC-001")
    mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.search_tickets", return_value=[])

    mock_create = mocker.patch("ops_pilot.tools.ticket_toolchain.ticket_repository.create_ticket")
    mock_create.return_value = mock_ticket
    
    result = create_ticket_tool.invoke({
        "employee_id": "E001",
        "title": "broken laptop",
        "description": "screen is cracked",
        "status": "Open",
        "priority": "Low",
        "category": "Hardware",
        "assigned_to": "A001",
        "notes": ""
    })
    
    assert result.id == "INC-001"
    mock_create.assert_called_once()
    # verify it looked for SYS-HW
    args, kwargs = mock_create.call_args
    assert args[0].system_id == "SYS-HW"

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
