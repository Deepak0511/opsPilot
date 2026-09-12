import pytest
from ops_pilot.repository.employee_repository import (
    create_employee,
    find_employee_by_id,
    find_employee_by_email,
    search_employees_by_name,
    find_employees_by_department,
    count_employees_by_department,
)
from ops_pilot.models.employee import Employee

@pytest.fixture
def sample_employee():
    return Employee(
        id="E001",
        name="John Doe",
        email="john.doe@example.com",
        department="IT",
        role="Engineer",
        device_type="Laptop",
        device_id="L-123"
    )

def test_create_and_find_employee_by_id(db_connection, sample_employee):
    # Test create
    created = create_employee(sample_employee)
    assert created.id == sample_employee.id
    
    # Test find by id
    found = find_employee_by_id(sample_employee.id)
    assert found is not None
    assert found.name == "John Doe"

def test_find_employee_by_email(db_connection, sample_employee):
    create_employee(sample_employee)
    
    found = find_employee_by_email("john.doe@example.com")
    assert found is not None
    assert found.id == sample_employee.id
    
    # Test case insensitivity
    found_upper = find_employee_by_email("JOHN.DOE@EXAMPLE.COM")
    assert found_upper is not None
    assert found_upper.id == sample_employee.id
    
    # Test not found
    not_found = find_employee_by_email("nobody@example.com")
    assert not_found is None

def test_search_employees_by_name(db_connection, sample_employee):
    create_employee(sample_employee)
    
    # Test partial match
    results = search_employees_by_name("John")
    assert len(results) == 1
    assert results[0].id == sample_employee.id
    
    # Test case insensitivity
    results = search_employees_by_name("doe")
    assert len(results) == 1
    
    # Test no match
    results = search_employees_by_name("Jane")
    assert len(results) == 0

def test_department_queries(db_connection, sample_employee):
    create_employee(sample_employee)
    
    emp2 = sample_employee.model_copy(update={"id": "E002", "name": "Jane Smith", "email": "jane@example.com"})
    create_employee(emp2)
    
    emp3 = sample_employee.model_copy(update={"id": "E003", "name": "Bob", "email": "bob@hr.com", "department": "HR"})
    create_employee(emp3)
    
    # Test count
    count_it = count_employees_by_department("IT")
    assert count_it == 2
    
    count_hr = count_employees_by_department("hr")
    assert count_hr == 1
    
    # Test find
    it_emps = find_employees_by_department("IT", offset=0, limit=10)
    assert len(it_emps) == 2
    
    # Test pagination
    it_emps_page = find_employees_by_department("IT", offset=0, limit=1)
    assert len(it_emps_page) == 1
    assert it_emps_page[0].id == "E001"
