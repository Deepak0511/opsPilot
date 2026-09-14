from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.system import System
from ops_pilot.utils.logger import log

import ops_pilot.repository.system_repository as system_repository
from ops_pilot.utils.error_handler import handle_tool_errors
from ops_pilot.utils import validators


@tool
@handle_tool_errors
def count_systems_tool(keyword: Optional[str] = None, status: Optional[str] = None) -> int:
    """Returns the count of systems matching the given filters.
    Pass activity names (e.g., 'timesheet', 'payroll') into the 'keyword' argument to search system names and description tags.
    Call this BEFORE search_systems to gauge result-set size.
    Helps the AI decide whether to refine filters or fetch directly.
    """
    log.info(f"Tool invoked: count_systems_tool(keyword={keyword}, status={status})")
    if keyword:
        keyword = validators.validate_not_empty(keyword, "keyword")
    if status:
        status = validators.validate_not_empty(status, "status")
    return system_repository.count_systems(keyword=keyword, status=status)


@tool
@handle_tool_errors
def search_systems_tool(keyword: Optional[str] = None, status: Optional[str] = None) -> list[System]:
    """Searches for IT systems by optional keyword and/or status.
    Pass activity names (e.g., 'timesheet', 'payroll') into the 'keyword' argument to search system names and description tags.
    At least one parameter must be provided. The goal is to narrow down to a single system
    whose ID can then be used for ticket creation or lookup.
    Use count_systems first to check result-set size.
    """
    log.info(f"Tool invoked: search_systems_tool(keyword={keyword}, status={status})")
    if keyword:
        keyword = validators.validate_not_empty(keyword, "keyword")
    if status:
        status = validators.validate_not_empty(status, "status")

    if not any([keyword, status]):
        raise ValueError("At least one search parameter (keyword or status) must be provided.")

    results: list[System] = []
    if keyword and status:
        by_keyword = system_repository.search_systems_by_keyword(keyword)
        results = [s for s in by_keyword if s.status and s.status.lower() == status.lower()]
    elif keyword:
        results = system_repository.search_systems_by_keyword(keyword)
    elif status is not None:
        results = system_repository.search_systems_by_status(status)

    if not results:
        raise ValueError("No systems found for your query. Please ask the user to clarify their input or check your spelling.")

    return results