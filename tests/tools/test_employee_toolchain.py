import pytest
from ops_pilot.tools.employee_toolchain import (
    search_employee_tool,
    count_employees_in_department_tool,
    get_employees_by_department_tool,
)
from ops_pilot.models.employee import Employee

@pytest.fixture
def mock_employee():
    return Employee(
        id="E001",
        name="John Doe",
        email="john.doe@example.com",
        department="IT",
        role="Engineer",
        device_type="Laptop",
        device_id="L-123"
    )

def test_search_employee_tool_by_email(mocker, mock_employee):
    # Mock repository
    mock_find_by_email = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employee_by_email")
    mock_find_by_email.return_value = mock_employee
    
    # Actually calling the tool requires invoking it. Since it's decorated with @tool, we can call it directly.
    # Note: in newer langchain versions, we might need to invoke .invoke() or just call it directly.
    # We will call it directly.
    results = search_employee_tool.invoke({"email": "john.doe@example.com"})
    
    assert len(results) == 1
    assert results[0].id == "E001"
    mock_find_by_email.assert_called_once_with("john.doe@example.com")

def test_search_employee_tool_by_name(mocker, mock_employee):
    mock_find_by_email = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employee_by_email")
    mock_find_by_email.return_value = None
    
    mock_search_by_name = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.search_employees_by_name")
    mock_search_by_name.return_value = [mock_employee]
    
    results = search_employee_tool.invoke({"name": "John Doe"})
    
    assert len(results) == 1
    assert results[0].id == "E001"
    mock_search_by_name.assert_called_once_with("John Doe")

def test_search_employee_tool_no_args():
    result = search_employee_tool.invoke({})
    assert isinstance(result, str) and result.startswith("Validation Error")

def test_search_employee_tool_not_found(mocker):
    mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employee_by_email", return_value=None)
    mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.search_employees_by_name", return_value=[])
    
    result = search_employee_tool.invoke({"name": "Nobody"})
    assert isinstance(result, str) and result.startswith("Validation Error")

def test_search_employee_tool_ambiguous(mocker, mock_employee):
    # Mock search to return 4 employees
    mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employee_by_email", return_value=None)
    mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.search_employees_by_name", return_value=[mock_employee] * 4)
    
    result = search_employee_tool.invoke({"name": "John Doe"})
    # Should return Validation Error for ambiguous results > 3
    assert isinstance(result, str) and "Ambiguous search" in result

def test_search_employee_tool_by_id(mocker, mock_employee):
    mock_find_by_id = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employee_by_id")
    mock_find_by_id.return_value = mock_employee

    result = search_employee_tool.invoke({"employee_id": "E001"})
    
    assert len(result) == 1
    assert result[0].id == "E001"
    mock_find_by_id.assert_called_once_with("E001")

def test_count_employees_in_department_tool(mocker):
    mock_count = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.count_employees_by_department")
    mock_count.return_value = 5
    
    result = count_employees_in_department_tool.invoke({"department": "IT"})
    assert result == 5
    mock_count.assert_called_once_with("IT")

def test_get_employees_by_department_tool(mocker, mock_employee):
    mock_find = mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employees_by_department")
    mock_find.return_value = [mock_employee]
    
    results = get_employees_by_department_tool.invoke({"department": "IT", "offset": 0, "limit": 10})
    assert len(results) == 1
    assert results[0].id == "E001"
    mock_find.assert_called_once_with("IT", 0, 10)

def test_get_employees_by_department_tool_not_found(mocker):
    mocker.patch("ops_pilot.tools.employee_toolchain.employee_repository.find_employees_by_department", return_value=[])
    result = get_employees_by_department_tool.invoke({"department": "HR"})
    assert isinstance(result, str) and result.startswith("Validation Error")
