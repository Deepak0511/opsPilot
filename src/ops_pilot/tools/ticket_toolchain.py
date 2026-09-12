# Set of tools for creating, deleting, updating and searching tickets.
from datetime import datetime
from datetime import date
from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.ticket import Ticket

import ulid
import dateparser
import ops_pilot.repository.employee_repository as employee_repository
import ops_pilot.repository.ticket_repository as ticket_repository
import ops_pilot.repository.knowledge_base_repository as knowledge_base_repository
import ops_pilot.repository.system_repository as system_repository


## Search Tools for Tickets

##Scenario 1: User has Ticket-ID
@tool
def search_ticket_by_id(ticket_id: str) -> Ticket:
    """Searches for a ticket by its ID."""
    ticket = ticket_repository.find_ticket_by_id(ticket_id)
    if not ticket:
        raise ValueError(f"Ticket with ID {ticket_id} does not exist.")
    return ticket

@tool
def search_tickets(employee_id: str, title: Optional[str] = None, description: Optional[str] = None,  
                   category: Optional[str] = None, system_id: Optional[str] = None, 
                   assigned_to: Optional[str] = None, created_date_str: Optional[str] = None) -> list[Ticket]:
    """Searches for tickets belonging to an employee, narrowing results through a waterfall of filters.

    Filters are tiered — strict filters run first in a single DB query; if more than one ticket
    remains, loose filters are applied one-by-one to try narrowing further:

      Strict + Medium (DB query — applied together, skipped when absent):
        - employee_id  (required) — resolved ID. Use search_employee beforehand.
        - system_id    (strict)   — resolved ID. Use search_systems beforehand.
        - assigned_to  (strict)   — resolved employee ID of the IT person. Use search_employee beforehand.
        - category     (medium)   — passed as-is.
        - created_date_str (medium) — natural-language date: 'today', 'yesterday', '2 days ago', 'last Monday'.

      Loose (Python-side, best-effort — only tried if multiple tickets remain):
        - title        — substring match. Skipped if it would eliminate all remaining results.
        - description  — substring match. Skipped if it would eliminate all remaining results.

    Strict parameters must be pre-resolved IDs — never pass raw names.
    Gather as much detail as the user can provide before calling this tool.
    At least one optional parameter must be supplied alongside employee_id.
    May return multiple tickets if filters cannot narrow to a single result.
    """
    if not any([title, description, category, system_id, assigned_to, created_date_str]):
        raise ValueError("At least one search parameter besides employee_id must be provided.")

    created_date = string_to_date(created_date_str)

    # Strict + Medium pass — let the DB do the heavy lifting
    tickets = ticket_repository.search_tickets(
        employee_id=employee_id,
        system_id=system_id,
        assigned_to=assigned_to,
        category=category,
        start_date=created_date.isoformat() if created_date else None,
    )

    if not tickets:
        raise ValueError("No tickets found matching the provided criteria.")

    if len(tickets) == 1:
        return tickets

    # Loose filters — best-effort narrowing, preserves current set if a filter matches nothing
    if title:
        narrowed = [t for t in tickets if title.lower() in t.title.lower()]
        if narrowed:
            tickets = narrowed
        if len(tickets) == 1:
            return tickets

    if description:
        narrowed = [t for t in tickets if description.lower() in t.description.lower()]
        if narrowed:
            tickets = narrowed

    return tickets


## CRUD Operations for Tickets
@tool
def create_ticket(employee_id: str, title: str, description: str, 
                  status: str, priority: str, category: str, 
                  system_id: str, assigned_to: str, notes: str) -> Ticket:
    """Creates a new ticket in the system. This tool however is very strict as it requires System ID and Employee ID 
        beforehand. To keep things modular, Employee ID and System ID lookup can be done using their respective tools
        and repositories.
    """
    # Validate employee_id and system_id
    employee = employee_repository.find_employee_by_id(employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")

    # We can use "Other" as a default system if the user is not sure of it.
    system = system_repository.find_system_by_id(system_id)
    if not system:
        raise ValueError(f"System with ID {system_id} does not exist.")
    
    # Create the ticket object
    ticket = Ticket(
        id=str(ulid.new()),
        employee_id=employee_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        category=category,
        system_id=system_id,
        assigned_to=assigned_to,
        created_date=datetime.now(),
        updated_date=datetime.now(),
        notes=notes
    )
    
    # Persist the ticket in the database
    created_ticket = ticket_repository.create_ticket(ticket)
    return created_ticket

## Update ticket - only status, priority, assigned_to and notes can be updated.
@tool
def update_ticket(ticket_id: str, status: Optional[str] = None, priority: Optional[str] = None,
                    assigned_to: Optional[str] = None, notes: Optional[str] = None) -> Ticket:
        """Updates an existing ticket in the system. Only status, priority, assigned_to and notes can be updated."""
        ticket = ticket_repository.find_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket with ID {ticket_id} does not exist.")
    
        # Update the fields if provided
        if status:
            ticket.status = status
        if priority:
            ticket.priority = priority
        if assigned_to:
            ticket.assigned_to = assigned_to
        if notes:
            ticket.notes = notes
    
        # Update the updated_date to now
        ticket.updated_date = datetime.now()
    
        # Persist the updated ticket in the database
        updated_ticket = ticket_repository.update_ticket(ticket)
        return updated_ticket





##############################################
########Local Utilities ###########
def string_to_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None

    parsed = dateparser.parse(value)

    if parsed is None:
        return None

    return parsed.date()