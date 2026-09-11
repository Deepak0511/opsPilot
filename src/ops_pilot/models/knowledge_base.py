# Data Model
from pydantic import BaseModel, Field
from typing import Optional

class KnowledgeBase(BaseModel):
    id: str = Field(..., min_length=1, description="Unique Identification-alphanumeric")
    title: str = Field(..., min_length=2, max_length=200, description="Title of the knowledge base article")
    category: str = Field(..., min_length=2, max_length=100, description="Category of the knowledge base article")
    content: str = Field(..., min_length=10, description="Content of the knowledge base article")
    Incident_id: Optional[str] = Field(None, description="Associated incident ID")
    tags: list[str] = Field(..., description="List of tags for the knowledge base article")