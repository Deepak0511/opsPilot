from typing import Optional
from langchain_core.tools import tool
from ops_pilot.models.system import System

import ops_pilot.repository.system_repository as system_repository


@tool
def count_systems(name: Optional[str] = None, status: Optional[str] = None) -> int:
    """Returns the count of systems matching the given filters.
    Call this BEFORE search_systems to gauge result-set size.
    Helps the AI decide whether to refine filters or fetch directly.
    """
    return system_repository.count_systems(name=name, status=status)


@tool
def search_systems(name: Optional[str] = None, status: Optional[str] = None) -> list[System]:
    """Searches for IT systems by optional name and/or status.
    At least one parameter must be provided. The goal is to narrow down to a single system
    whose ID can then be used for ticket creation or lookup.
    Use count_systems first to check result-set size.
    """
    if not any([name, status]):
        raise ValueError("At least one search parameter (name or status) must be provided.")

    results: list[System] = []
    if name and status:
        by_name = system_repository.search_systems_by_name(name)
        results = [s for s in by_name if s.status and s.status.lower() == status.lower()]
    elif name:
        results = system_repository.search_systems_by_name(name)
    elif status is not None:
        results = system_repository.search_systems_by_status(status)

    if not results:
        raise ValueError("No systems found matching the provided criteria.")

    return results