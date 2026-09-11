# Data Model
from datetime import date
from pydantic import BaseModel, Field
from google.genai._gaos.types.interactions import harmcategory
from typing import Optional

class Ticket(BaseModel):
    id: str = Field(..., min_length=1, description="Unique Identification-alphanumeric")
    employee_id: str= Field(..., min_length=1, description="Employee Id linked to thsi ticket")
    title: str
    description: str
    status: str
    priority: str
    category: str
    system_id: str # Tells where the problem is.
    assigned_to: str # employee_id Of the IT Support Person
    created_date: date
    updated_date: date
    notes: Optional[str] = None