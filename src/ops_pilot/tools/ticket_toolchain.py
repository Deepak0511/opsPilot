# Set of tools for creating, deleting, updating and searching tickets.
from datetime import datetime
from datetime import date
from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.ticket import Ticket
from ops_pilot.utils.logger import log, audit_log

import ulid
import dateparser
import ops_pilot.repository.employee_repository as employee_repository
import ops_pilot.repository.ticket_repository as ticket_repository
import ops_pilot.repository.knowledge_base_repository as knowledge_base_repository
import ops_pilot.repository.system_repository as system_repository
from ops_pilot.utils.error_handler import handle_tool_errors
from ops_pilot.utils import validators
from ops_pilot.utils.id_generator import generate_ticket_id


## Search Tools for Tickets

##Scenario 1: User has Ticket-ID
@tool
@handle_tool_errors
def search_ticket_by_id_tool(ticket_id: str) -> Ticket:
    """Searches for a ticket by its ID."""
    log.info(f"Tool invoked: search_ticket_by_id_tool(ticket_id={ticket_id})")
    ticket_id = validators.validate_id_format(ticket_id, "ticket_id")
    ticket = ticket_repository.find_ticket_by_id(ticket_id)
    if not ticket:
        raise ValueError(f"Ticket with ID {ticket_id} does not exist.")
    return ticket

@tool
@handle_tool_errors
def search_tickets_tool(employee_id: str, title: Optional[str] = None, description: Optional[str] = None,  
                   category: Optional[str] = None, system_id: Optional[str] = None, 
                   assigned_to: Optional[str] = None, created_date_str: Optional[str] = None) -> list[Ticket]:
    """Searches for tickets belonging to an employee, narrowing results through a waterfall of filters.

    Filters are tiered — strict filters run first in a single DB query; if more than one ticket
    remains, loose filters are applied one-by-one to try narrowing further:

      Strict + Medium (DB query — applied together, skipped when absent):
        - employee_id  (required) — resolved ID. Use search_employee_tool beforehand.
        - system_id    (strict)   — resolved ID. Use search_systems_tool beforehand.
        - assigned_to  (strict)   — resolved employee ID of the IT person. Use search_employee_tool beforehand.
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
    log.info(f"Tool invoked: search_tickets_tool(employee_id={employee_id}, title={title}, category={category}, system_id={system_id})")
    employee_id = validators.validate_id_format(employee_id, "employee_id")
    if system_id:
        system_id = validators.validate_id_format(system_id, "system_id")
    if assigned_to:
        assigned_to = validators.validate_id_format(assigned_to, "assigned_to")

    if not any([title, description, category, system_id, assigned_to, created_date_str]):
        raise ValueError("At least one search parameter besides employee_id must be provided.")

    try:
        created_date = string_to_date(created_date_str)
    except Exception:
        raise ValueError(f"Could not parse date: {created_date_str}")

    # Strict + Medium pass — let the DB do the heavy lifting
    tickets = ticket_repository.search_tickets(
        title=None, description=None, category=category,
        employee_id=employee_id, system_id=system_id, assigned_to=assigned_to,
        start_date=created_date.isoformat() if created_date else None, 
        end_date=created_date.isoformat() if created_date else None
    )

    if not tickets:
        raise ValueError("No tickets found for your query. Please ask the user to clarify or broaden their search.")

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
@handle_tool_errors
def create_ticket_tool(employee_id: str, title: str, description: str, 
                  status: str, category: str, ticket_type: str,
                  priority: Optional[str] = None, assigned_to: Optional[str] = None,
                  notes: Optional[str] = None, system_id: Optional[str] = None) -> Ticket:
    """Creates a new ticket in the system. This tool however is very strict as it requires System ID and Employee ID 
        beforehand. To keep things modular, Employee ID and System ID lookup can be done using their respective tools
        and repositories.

        Priority and assignment are optional. If omitted, priority is inferred from
        the issue severity and the first employee in the IT department is assigned.
    """
    log.info(f"Tool invoked: create_ticket_tool(employee_id={employee_id}, title={title}, system_id={system_id})")
    # Validate fields
    employee_id = validators.validate_id_format(employee_id, "employee_id")
    title = validators.validate_not_empty(title, "title")
    description = validators.validate_not_empty(description, "description")
    category = validators.validate_not_empty(category, "category")
    status = validators.validate_status(status)
    ticket_type = validators.validate_ticket_type(ticket_type)
    priority = validators.validate_priority(priority or infer_priority(title, description, category))
    assigned_to = assigned_to or get_default_assignee()
    assigned_to = validators.validate_id_format(assigned_to, "assigned_to")

    if not system_id or system_id.lower() in ("none", "null", ""):
        # Infer fallback
        if "hardware" in category.lower() or any(term in title.lower() or term in description.lower() for term in ["laptop", "desktop", "monitor", "mouse", "keyboard"]):
            system_id = "SYS-HW"
        else:
            system_id = "SYS-OTHER"
    else:
        system_id = validators.validate_id_format(system_id, "system_id")

    # Validate employee_id and system_id
    employee = employee_repository.find_employee_by_id(employee_id)
    if not employee:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")

    system = system_repository.find_system_by_id(system_id)
    if not system:
        raise ValueError(f"System with ID {system_id} does not exist.")
        
    # Check for duplicate tickets
    existing_tickets = ticket_repository.search_tickets(employee_id=employee_id, system_id=system_id)
    for t in existing_tickets:
        if t.status in ["Open", "In Progress"] and t.title.lower() == title.lower():
            raise ValueError(f"Duplicate Ticket Detected: A ticket with the same title is already open (Ticket ID: {t.id}). Please inform the user.")
    
    # Generate ID
    conn = ticket_repository.get_connection()
    try:
        new_id = generate_ticket_id(conn, ticket_type)
    finally:
        conn.close()

    # Create the ticket object
    ticket = Ticket(
        id=new_id,
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
    audit_log.info(f"Ticket {created_ticket.id} created by employee {employee_id} for system {system_id}")
    return created_ticket


def infer_priority(title: str, description: str, category: str) -> str:
    """Apply the default severity matrix when the user does not specify priority."""
    text = f"{title} {description} {category}".lower()
    if any(term in text for term in ("security breach", "data loss", "ransomware", "all users", "outage")):
        return "Critical"
    if any(term in text for term in ("cannot work", "can't work", "unable to work", "blocked", "down", "unavailable")):
        return "High"
    if any(term in text for term in ("question", "how do i", "request", "access")):
        return "Low"
    return "Medium"


def get_default_assignee() -> str:
    """Assign new tickets to the first available employee in the IT department."""
    employees = employee_repository.find_employees_by_department("IT Support", offset=0, limit=1)
    if not employees:
        raise ValueError("No employees are available in the IT department for ticket assignment.")
    return employees[0].id

## Update ticket - only status, priority, assigned_to and notes can be updated.
@tool
@handle_tool_errors
def update_ticket_tool(ticket_id: str, status: Optional[str] = None, priority: Optional[str] = None,
                    assigned_to: Optional[str] = None, notes: Optional[str] = None) -> Ticket:
        """Updates an existing ticket in the system. Only status, priority, assigned_to and notes can be updated."""
        log.info(f"Tool invoked: update_ticket_tool(ticket_id={ticket_id}, status={status}, priority={priority})")
        ticket_id = validators.validate_id_format(ticket_id, "ticket_id")
        ticket = ticket_repository.find_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket with ID {ticket_id} does not exist.")
    
        # Update the fields if provided
        if status:
            ticket.status = validators.validate_status(status)
        if priority:
            ticket.priority = validators.validate_priority(priority)
        if assigned_to:
            ticket.assigned_to = validators.validate_id_format(assigned_to, "assigned_to")
        if notes:
            ticket.notes = notes
    
        # Update the updated_date to now
        ticket.updated_date = datetime.now()
    
        # Persist the updated ticket in the database
        updated_ticket = ticket_repository.update_ticket(ticket)
        audit_log.info(f"Ticket {updated_ticket.id} updated (status={status}, priority={priority})")
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