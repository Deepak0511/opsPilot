import pytest
from ops_pilot.utils.id_generator import (
    generate_employee_id,
    generate_ticket_id,
    generate_kb_id,
    VALID_TICKET_TYPES,
)

def test_generate_employee_id():
    emp_id = generate_employee_id()
    assert isinstance(emp_id, str)
    assert len(emp_id) == 6
    # Ensure it only uses friendly chars
    friendly_chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    assert all(c in friendly_chars for c in emp_id)

    emp_id_long = generate_employee_id(length=10)
    assert len(emp_id_long) == 10

def test_generate_ticket_id(db_connection):
    # First call
    ticket_id = generate_ticket_id(db_connection, "INC")
    assert ticket_id == "INC-001"
    
    # Second call increments
    ticket_id = generate_ticket_id(db_connection, "INC")
    assert ticket_id == "INC-002"
    
    # Different type starts at 1
    ticket_id = generate_ticket_id(db_connection, "RIT")
    assert ticket_id == "RIT-001"

def test_generate_ticket_id_invalid_type(db_connection):
    with pytest.raises(ValueError, match="Invalid ticket type 'XYZ'"):
        generate_ticket_id(db_connection, "XYZ")

def test_generate_kb_id(db_connection):
    kb_id = generate_kb_id(db_connection)
    assert kb_id == "KB-001"
    
    kb_id = generate_kb_id(db_connection)
    assert kb_id == "KB-002"
