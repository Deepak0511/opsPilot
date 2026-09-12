# Agent State which flows through the entire graph.
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages



class AgentState(BaseModel):
    """Shared state that travels through the graph. Like a DTO passed between services."""
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    current_branch: Optional[str] = None
    next_node: Optional[str] = None
    # ✅ Validates types at runtime — wrong types raise ValidationError
    # ✅ default_factory=list gives a clean empty state without manual {"messages": []}


# # ----- Tools -------------

# tools = [
#     search_employee,
#     search_ticket_by_id,
#     create_ticket,
#     search_knowledge_base,
#     search_systems,
# ]

# ------- Bind tools with LLM -----------
# llm = load_llm()
# llm_with_tools = llm.bind_tools(tools)