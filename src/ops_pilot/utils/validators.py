import re
from typing import Any, Optional

VALID_STATUSES = {"Open", "In Progress", "Resolved", "Closed", "On Hold"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}

def validate_not_empty(value: Optional[str], field_name: str) -> str:
    """Ensures a string is provided and not purely whitespace."""
    if not value or not value.strip():
        raise ValueError(f"'{field_name}' must be provided and cannot be empty.")
    return value.strip()

def validate_id_format(value: Optional[str], field_name: str) -> str:
    """Ensures an ID is alphanumeric and may contain hyphens."""
    value = validate_not_empty(value, field_name)
    if not re.match(r"^[a-zA-Z0-9\-]+$", value):
        raise ValueError(f"'{field_name}' has an invalid format. Only alphanumeric characters and hyphens are allowed.")
    return value

def validate_status(value: Optional[str]) -> str:
    """Ensures the status is one of the allowed ITIL standard values."""
    value = validate_not_empty(value, "status")
    # Title-case it to handle cases like 'open' -> 'Open'
    value = value.title() if value.lower() != "in progress" else "In Progress"
    # Wait, 'on hold' -> 'On Hold', 'in progress' -> 'In Progress'
    # Actually a dict mapping is safer
    mapping = {s.lower(): s for s in VALID_STATUSES}
    mapped = mapping.get(value.lower())
    if not mapped:
        raise ValueError(f"Invalid status '{value}'. Allowed values are: {', '.join(VALID_STATUSES)}.")
    return mapped

def validate_priority(value: Optional[str]) -> str:
    """Ensures the priority is one of the allowed values."""
    value = validate_not_empty(value, "priority")
    mapping = {p.lower(): p for p in VALID_PRIORITIES}
    mapped = mapping.get(value.lower())
    if not mapped:
        raise ValueError(f"Invalid priority '{value}'. Allowed values are: {', '.join(VALID_PRIORITIES)}.")
    return mapped
