# Data Model
from pydantic import BaseModel, Field
from typing import Optional

class System(BaseModel):
    id: str = Field(..., min_length=1, description="Unique Identification-alphanumeric")
    name: str = Field(..., min_length=2, max_length=100, description="Name of the system")
    status: str = Field(..., min_length=2, max_length=50, description="Current status of the system")
    description: Optional[str] = Field(None, max_length=500, description="Description of the system")
    last_checked: Optional[str] = Field(None, description="Timestamp of the last check performed on the system")