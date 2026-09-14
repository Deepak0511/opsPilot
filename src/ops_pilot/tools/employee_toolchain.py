from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.employee import Employee
from ops_pilot.utils.logger import log

import ops_pilot.repository.employee_repository as employee_repository
from ops_pilot.utils.error_handler import handle_tool_errors
from ops_pilot.utils import validators


@tool
@handle_tool_errors
def search_employee_tool(employee_id: Optional[str] = None, name: Optional[str] = None, email: Optional[str] = None,
                    department: Optional[str] = None) -> list[Employee]:
    """Searches for employees by ID, name, email, or department. At least one parameter must be provided.
    Use this to resolve a person's identity before creating or assigning tickets.
    Returns a list — if more than one result, ask the user to refine.
    """
    log.info(f"Tool invoked: search_employee_tool(employee_id={employee_id}, name={name}, email={email}, department={department})")
    if employee_id:
        employee_id = validators.validate_id_format(employee_id, "employee_id")
    if name:
        name = validators.validate_not_empty(name, "name")
    if email:
        email = validators.validate_not_empty(email, "email")
    if department:
        department = validators.validate_not_empty(department, "department")

    if not any([employee_id, name, email, department]):
        raise ValueError("At least one search parameter must be provided.")

    results: list[Employee] = []

    if employee_id:
        emp = employee_repository.find_employee_by_id(employee_id)
        if emp:
            return [emp]

    if email:
        emp = employee_repository.find_employee_by_email(email)
        if emp:
            return [emp]

    if name:
        results = employee_repository.search_employees_by_name(name)
    elif department:
        # Fallback if only department is provided, fetch all in department (limited)
        results = employee_repository.find_employees_by_department(department, offset=0, limit=10)

    if department and name:
        results = [e for e in results if e.department and e.department.lower() == department.lower()]

    if not results:
        raise ValueError("No results found for your query. Please ask the user to clarify their input or check your spelling.")

    if len(results) > 3:
        raise ValueError(f"Ambiguous search: found {len(results)} results. Please ask the user to confirm the exact employee_id.")

    return results


@tool
@handle_tool_errors
def count_employees_in_department_tool(department: str) -> int:
    """Returns the number of employees in a department.
    Call this BEFORE get_employees_by_department to check the result-set size.
    If the count exceeds 10, use pagination via offset/limit.
    """
    log.info(f"Tool invoked: count_employees_in_department_tool(department={department})")
    department = validators.validate_not_empty(department, "department")
    return employee_repository.count_employees_by_department(department)


@tool
@handle_tool_errors
def get_employees_by_department_tool(department: str, offset: int = 0, limit: int = 10) -> list[Employee]:
    """Fetches employees belonging to a department with pagination.
    Always call count_employees_in_department first to know total size.
    Default page size is 10.
    """
    log.info(f"Tool invoked: get_employees_by_department_tool(department={department}, offset={offset}, limit={limit})")
    department = validators.validate_not_empty(department, "department")
    employees = employee_repository.find_employees_by_department(department, offset, limit)
    if not employees:
        raise ValueError(f"No employees found in department '{department}'.")
    return employees