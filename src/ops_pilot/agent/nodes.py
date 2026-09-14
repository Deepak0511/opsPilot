
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
from ops_pilot.tools.employee_toolchain import search_employee_tool
from ops_pilot.agent.state import AgentState, TriageDecision
from langchain_core.messages import SystemMessage
from typing import cast
from ops_pilot.prompts.system_prompt import (
    TRIAGE_MANAGER_PROMPT,
    KNOWLEDGE_BASE_MANAGER_PROMPT,
    INFRASTRUCTURE_MANAGER_PROMPT,
    TICKET_READER_MANAGER_PROMPT,
    TICKET_LOGGER_MANAGER_PROMPT,
)
from ops_pilot.utils.large_language_models import load_llm
from ops_pilot.utils.logger import log
import re

# ── KB Node: can ONLY search knowledge base ──
kb_tools = [search_knowledge_base_tool, count_knowledge_base_articles_tool]
kb_llm = load_llm().bind_tools(kb_tools)

def kb_node(state: AgentState) -> dict:
    log.info("Agent entered node: kb_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(KNOWLEDGE_BASE_MANAGER_PROMPT, state))
    response = kb_llm.invoke([sys_msg] + state.messages)   # This LLM can ONLY call KB tools
    log.debug(f"kb_node response: {response}")
    return {"messages": [response], "current_branch": "kb_node"}


# ── Infra Node: can ONLY check system status ──
infra_tools = [search_systems_tool, count_systems_tool]
infra_llm = load_llm().bind_tools(infra_tools)

def infra_node(state: AgentState) -> dict:
    log.info("Agent entered node: infra_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(INFRASTRUCTURE_MANAGER_PROMPT, state))
    response = infra_llm.invoke([sys_msg] + state.messages)  # Can ONLY check systems
    log.debug(f"infra_node response: {response}")
    return {"messages": [response], "current_branch": "infra_node"}


# ── Ticket Reader: can search tickets and resolve lookup identifiers ──
ticket_read_tools = [
    search_ticket_by_id_tool,
    search_tickets_tool,
    search_employee_tool,
    search_systems_tool,
]
ticket_read_llm = load_llm().bind_tools(ticket_read_tools)

def ticket_read_node(state: AgentState) -> dict:
    log.info("Agent entered node: ticket_read_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(TICKET_READER_MANAGER_PROMPT, state))
    response = ticket_read_llm.invoke([sys_msg] + state.messages)  # Can ONLY read, never create
    log.debug(f"ticket_read_node response: {response}")
    return {"messages": [response], "current_branch": "ticket_read_node"}


# ── Ticket Logger: can write tickets and resolve required identifiers ──
ticket_write_tools = [
    create_ticket_tool,
    update_ticket_tool,
    search_employee_tool,
    search_systems_tool,
]
ticket_write_llm = load_llm().bind_tools(ticket_write_tools)

def ticket_logger_node(state: AgentState) -> dict:
    log.info("Agent entered node: ticket_logger_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(TICKET_LOGGER_MANAGER_PROMPT, state))
    response = ticket_write_llm.invoke([sys_msg] + state.messages)  # Can ONLY write tickets
    log.debug(f"ticket_logger_node response: {response}")
    return {"messages": [response], "current_branch": "ticket_logger_node"}


triage_llm = load_llm()  # No tools bound — it can only think and respond
structured_triage_llm = triage_llm.with_structured_output(TriageDecision)

def _prompt_with_routing_context(prompt: str, state: AgentState) -> str:
    if not state.routing_reason:
        return prompt
    return (
        f"{prompt}\n\n"
        "Internal triage context (do not quote directly to the user):\n"
        f"{state.routing_reason}"
    )

def triage_node(state: AgentState) -> dict:
    """Classifies the user's intent. No tools — just reasoning."""
    log.info("Agent entered node: triage_node")
    sys_msg = SystemMessage(content=TRIAGE_MANAGER_PROMPT)
    user_request = _latest_human_request(state)
    decision = cast(
        TriageDecision,
        structured_triage_llm.invoke([sys_msg] + state.messages),
    )
    if decision.next_node == "ticket_logger_node" and _is_guidance_request(user_request):
        decision = decision.model_copy(
            update={
                "next_node": "infra_node",
                "routing_reason": "The user is asking for procedural guidance, so gather system context before the KB step.",
            }
        )
    log.info(f"Triage routed to: {decision.next_node}; reason: {decision.routing_reason}")
    return {
        "next_node": decision.next_node,
        "routing_reason": decision.routing_reason,
    }


def _latest_human_request(state: AgentState) -> str:
    for message in reversed(state.messages):
        if message.type == "human":
            return str(message.content)
    return ""


def _is_guidance_request(request: str) -> bool:
    return bool(
        re.search(
            r"\b(?:how\s+(?:do|can)|what\s+are\s+the\s+steps|can\s+you\s+explain)\b",
            request,
            flags=re.IGNORECASE,
        )
    )

# Export all tools for the shared ToolNode. Deduplicate by tool name because
# LangChain tool objects themselves are unhashable.
all_tools = []
tool_names = set()
for tool in kb_tools + infra_tools + ticket_read_tools + ticket_write_tools:
    if tool.name not in tool_names:
        all_tools.append(tool)
        tool_names.add(tool.name)


