import pytest
from datetime import date
from ops_pilot.repository.ticket_repository import (
    create_ticket,
    find_ticket_by_id,
    search_tickets_by_title,
    search_tickets_by_status,
    search_tickets_by_priority,
    search_tickets_by_category,
    search_tickets_by_employee_id,
    search_tickets_by_date_range,
    search_tickets_by_system_id,
    search_tickets,
    update_ticket,
    delete_ticket,
)
from ops_pilot.models.ticket import Ticket

@pytest.fixture
def sample_ticket():
    return Ticket(
        id="INC-001",
        employee_id="E001",
        title="Laptop won't boot",
        description="Blue screen of death on startup",
        status="Open",
        priority="High",
        category="Hardware",
        system_id="SYS-001",
        assigned_to="A001",
        created_date=date(2023, 10, 27),
        updated_date=date(2023, 10, 27),
        notes="Urgent"
    )

def test_create_and_find_ticket(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    
    found = find_ticket_by_id(sample_ticket.id)
    assert found is not None
    assert found.title == "Laptop won't boot"
    
def test_search_tickets_by_status(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    
    results = search_tickets_by_status("Open")
    assert len(results) == 1
    
    results = search_tickets_by_status("Closed")
    assert len(results) == 0

def test_search_tickets_by_priority(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    
    results = search_tickets_by_priority("High")
    assert len(results) == 1
    
def test_search_tickets_mega_function(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    
    # Test matching criteria
    results = search_tickets(title="boot", category="Hardware")
    assert len(results) >= 1
    
    # Test non-matching criteria
    results = search_tickets(title="boot", category="Software")
    assert len(results) == 0

def test_update_ticket(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    
    sample_ticket.status = "In Progress"
    update_ticket(sample_ticket)
    
    found = find_ticket_by_id(sample_ticket.id)
    assert found.status == "In Progress"

def test_delete_ticket(db_connection, sample_ticket):
    create_ticket(sample_ticket)
    delete_ticket(sample_ticket.id)
    
    found = find_ticket_by_id(sample_ticket.id)
    assert found is None
