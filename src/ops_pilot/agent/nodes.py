
# Each node gets its OWN LLM with ONLY the tools it should use
# This multi-node approach assures that even a weak LLM can follow the desired 
# workflow and not endup creating duplicate or previously seen issues.
from ops_pilot.tools.ticket_toolchain import update_ticket_tool
from ops_pilot.tools.ticket_toolchain import create_ticket_tool
from ops_pilot.tools.ticket_toolchain import search_tickets_tool
from ops_pilot.tools.ticket_toolchain import search_ticket_by_id_tool
from ops_pilot.tools.system_toolchain import count_systems_tool
from ops_pilot.tools.system_toolchain import search_systems_tool
from ops_pilot.tools.kb_toolchain import count_knowledge_base_articles_tool
from ops_pilot.tools.kb_toolchain import search_knowledge_base_tool
from ops_pilot.agent.state import AgentState
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from ops_pilot.prompts.system_prompt import (
    TRIAGE_MANAGER_PROMPT,
    KNOWLEDGE_BASE_MANAGER_PROMPT,
    INFRASTRUCTURE_MANAGER_PROMPT,
    TICKET_READER_MANAGER_PROMPT,
    TICKET_LOGGER_MANAGER_PROMPT,
)
from ops_pilot.utils.large_language_models import load_llm

# ── KB Node: can ONLY search knowledge base ──
kb_tools = [search_knowledge_base_tool, count_knowledge_base_articles_tool]
kb_llm = load_llm().bind_tools(kb_tools)

def kb_node(state: AgentState) -> dict:
    sys_msg = SystemMessage(content=KNOWLEDGE_BASE_MANAGER_PROMPT)
    response = kb_llm.invoke([sys_msg] + state["messages"])   # This LLM can ONLY call KB tools
    return {"messages": [response], "current_branch": "kb_node"}


# ── Infra Node: can ONLY check system status ──
infra_tools = [search_systems_tool, count_systems_tool]
infra_llm = load_llm().bind_tools(infra_tools)

def infra_node(state: AgentState) -> dict:
    sys_msg = SystemMessage(content=INFRASTRUCTURE_MANAGER_PROMPT)
    response = infra_llm.invoke([sys_msg] + state["messages"])  # Can ONLY check systems
    return {"messages": [response], "current_branch": "infra_node"}


# ── Ticket Reader: can ONLY search existing tickets ──
ticket_read_tools = [search_ticket_by_id_tool, search_tickets_tool]
ticket_read_llm = load_llm().bind_tools(ticket_read_tools)

def ticket_read_node(state: AgentState) -> dict:
    sys_msg = SystemMessage(content=TICKET_READER_MANAGER_PROMPT)
    response = ticket_read_llm.invoke([sys_msg] + state["messages"])  # Can ONLY read, never create
    return {"messages": [response], "current_branch": "ticket_read_node"}


# ── Ticket Logger: can ONLY create/update tickets ──
ticket_write_tools = [create_ticket_tool, update_ticket_tool]
ticket_write_llm = load_llm().bind_tools(ticket_write_tools)

def ticket_logger_node(state: AgentState) -> dict:
    sys_msg = SystemMessage(content=TICKET_LOGGER_MANAGER_PROMPT)
    response = ticket_write_llm.invoke([sys_msg] + state["messages"])  # Can ONLY write tickets
    return {"messages": [response], "current_branch": "ticket_logger_node"}

## So Who decides which node to go to ?##
# Answer:
## Triage node: LLM classifies the user's intent using Structured Output
class TriageDecision(BaseModel):
    next_node: str = Field(
        description="The next node to route to. Must be one of: kb_node, infra_node, ticket_read_node, ticket_logger_node"
    )

triage_llm = load_llm()  # No tools bound — it can only think and respond
structured_triage_llm = triage_llm.with_structured_output(TriageDecision)

def triage_node(state: AgentState) -> dict:
    """Classifies the user's intent. No tools — just reasoning."""
    sys_msg = SystemMessage(content=TRIAGE_MANAGER_PROMPT)
    decision = structured_triage_llm.invoke([sys_msg] + state["messages"])
    return {"next_node": decision.next_node}

# Export all tools for the shared ToolNode
all_tools = kb_tools + infra_tools + ticket_read_tools + ticket_write_tools


