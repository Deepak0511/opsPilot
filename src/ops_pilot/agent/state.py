# Agent State which flows through the entire graph.
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Literal



class AgentState(BaseModel):
    """Shared state that travels through the graph. Like a DTO passed between services."""
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    current_branch: Optional[str] = None
    next_node: Optional[str] = None
    # Context only; tools still validate every identifier independently.
    request_origin: Literal["human", "agent", "system"] = "human"




class TriageDecision(BaseModel):
    next_node: Literal[
        "kb_node",
        "infra_node",
        "ticket_read_node",
        "ticket_logger_node",
    ]