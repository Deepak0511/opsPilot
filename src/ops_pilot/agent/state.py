# Agent State which flows through the entire graph.
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Literal
from ops_pilot.models.system import System



class AgentState(BaseModel):
    """Shared state that travels through the graph. Like a DTO passed between services."""
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    current_branch: Optional[str] = None
    next_node: Optional[str] = None
    routing_reason: Optional[str] = None
    infrastructure_context_status: Optional[
        Literal["FOUND", "NOT_FOUND", "AMBIGUOUS", "CONFIRMATION_PENDING"]
    ] = None
    infrastructure_context: list[System] = Field(default_factory=list)
    # Diagnostic trace for the current user turn. The entry gate resets it
    # before each new turn; it is not a conversation-wide counter.
    completed_steps: list[str] = Field(default_factory=list)
    execution_count: int = 0
    pending_ticket_draft: Optional["TicketDraft"] = None
    awaiting_ticket_confirmation: bool = False
    ticket_confirmation_decision: Optional[
        Literal["CONFIRMED", "CANCELLED", "UNCLEAR"]
    ] = None
    # Context only; tools still validate every identifier independently.
    request_origin: Literal["human", "agent", "system"] = "human"




class TriageDecision(BaseModel):
    next_node: Literal[
        "INFRASTRUCTURE_LOOKUP_REQUEST",
        "KNOWLEDGE_BASE_LOOKUP_REQUEST",
        "TICKET_LOOKUP_REQUEST",
        "TICKET_ACTION_REQUEST",
    ]
    routing_reason: str = Field(
        description="Brief explanation for why this node was selected."
    )


class TicketDraft(BaseModel):
    """Persisted, user-visible intent for one ticket mutation. Call this tool to prepare the draft for confirmation. You MUST infer title, description, category, and status from the user's reported issue. ONLY ask the user for missing information if it is impossible to infer (e.g., employee_id)."""

    operation: Literal["CREATE", "UPDATE"]
    ticket_id: Optional[str] = None
    employee_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    ticket_type: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    system_id: Optional[str] = None
