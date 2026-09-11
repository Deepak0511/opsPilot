# Data Model
from pydantic import BaseModel, Field
from typing import Optional

class Employee(BaseModel):
    """Employee"""
    id: str = Field(..., min_length=1, description="Unique Identification-alphanumeric")
    name: str = Field(..., min_length=1)
    email: str
    department: str
    role: Optional[str] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None
