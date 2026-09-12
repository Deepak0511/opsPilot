from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.employee import Employee

import ops_pilot.repository.employee_repository as employee_repository


@tool
def search_employee(name: Optional[str] = None, email: Optional[str] = None,
                    department: Optional[str] = None) -> list[Employee]:
    """Searches for employees by name, email, or department. At least name or email must be provided.
    Use this to resolve a person's identity before creating or assigning tickets.
    Returns a list — if more than one result, ask the user to refine.
    """
    if not name and not email:
        raise ValueError("At least name or email must be provided.")

    results: list[Employee] = []

    if email:
        emp = employee_repository.find_employee_by_email(email)
        if emp:
            return [emp]

    if name:
        results = employee_repository.search_employees_by_name(name)

    if department and results:
        results = [e for e in results if e.department and e.department.lower() == department.lower()]

    if not results:
        raise ValueError("No employees found matching the provided criteria.")

    return results


@tool
def count_employees_in_department(department: str) -> int:
    """Returns the number of employees in a department.
    Call this BEFORE get_employees_by_department to check the result-set size.
    If the count exceeds 10, use pagination via offset/limit.
    """
    return employee_repository.count_employees_by_department(department)


@tool
def get_employees_by_department(department: str, offset: int = 0, limit: int = 10) -> list[Employee]:
    """Fetches employees belonging to a department with pagination.
    Always call count_employees_in_department first to know total size.
    Default page size is 10.
    """
    employees = employee_repository.find_employees_by_department(department, offset, limit)
    if not employees:
        raise ValueError(f"No employees found in department '{department}'.")
    return employees