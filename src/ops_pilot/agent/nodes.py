
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
from ops_pilot.agent.state import AgentState, TriageDecision, TicketDraft
from langchain_core.messages import SystemMessage
from langchain_core.messages import AIMessage
from typing import cast
from ops_pilot.prompts.system_prompt import (
    TRIAGE_MANAGER_PROMPT,
    KNOWLEDGE_BASE_MANAGER_PROMPT,
    INFRASTRUCTURE_MANAGER_PROMPT,
    TICKET_READ_MANAGER_PROMPT,
    TICKET_WRITE_MANAGER_PROMPT,
    INFRASTRUCTURE_KEYWORD_EXTRACTION_PROMPT
)
from ops_pilot.utils.large_language_models import load_llm
from ops_pilot.utils.logger import log
import ops_pilot.repository.system_repository as system_repository
import re

MAX_EXECUTION_STEPS = 200


def _step_update(state: AgentState, node_name: str, *, reset: bool = False) -> dict:
    """Record one node and bound execution within the current user turn."""
    prior_steps = [] if reset else state.completed_steps
    next_count = 1 if reset else state.execution_count + 1
    if next_count > MAX_EXECUTION_STEPS:
        trace = [*prior_steps, node_name]
        raise RuntimeError(
            "Graph exceeded the maximum execution steps: "
            f"{MAX_EXECUTION_STEPS}; trace={trace}; "
            f"next_node={state.next_node!r}; current_branch={state.current_branch!r}"
        )
    return {
        "completed_steps": [*prior_steps, node_name],
        "execution_count": next_count,
    }

# ── KB Node: can ONLY search knowledge base ──
kb_tools = [search_knowledge_base_tool, count_knowledge_base_articles_tool]
kb_llm = load_llm().bind_tools(kb_tools)

def kb_node(state: AgentState) -> dict:
    log.info("Agent entered node: kb_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(KNOWLEDGE_BASE_MANAGER_PROMPT, state))
    response = kb_llm.invoke([sys_msg] + state.messages)   # This LLM can ONLY call KB tools
    log.debug(f"kb_node response: {response}")
    return {
        "messages": [response],
        "current_branch": "KNOWLEDGE_BASE_MANAGER",
        **_step_update(state, "KNOWLEDGE_BASE_MANAGER"),
    }


# ── Infra Node: can ONLY check system status ──
infra_tools = [search_systems_tool, count_systems_tool]
infra_llm = load_llm().bind_tools(infra_tools)

def infra_node(state: AgentState) -> dict:
    log.info("Agent entered node: infra_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(INFRASTRUCTURE_MANAGER_PROMPT, state))
    response = infra_llm.invoke([sys_msg] + state.messages)  # Can ONLY check systems
    log.debug(f"infra_node response: {response}")
    return {
        "messages": [response],
        "current_branch": "INFRASTRUCTURE_MANAGER",
        **_step_update(state, "INFRASTRUCTURE_MANAGER"),
    }


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
    sys_msg = SystemMessage(content=_prompt_with_routing_context(TICKET_READ_MANAGER_PROMPT, state))
    response = ticket_read_llm.invoke([sys_msg] + state.messages)  # Can ONLY read, never create
    log.debug(f"ticket_read_node response: {response}")
    return {
        "messages": [response],
        "current_branch": "TICKET_READ_MANAGER",
        **_step_update(state, "TICKET_READ_MANAGER"),
    }


# ── Ticket Logger: can write tickets and resolve required identifiers ──
# Ticket manager prepares drafts with lookup tools; mutations run only after confirmation.
ticket_write_tools = [
    search_employee_tool,
    search_systems_tool,
    search_ticket_by_id_tool,
    search_tickets_tool,
    TicketDraft,
]
ticket_write_llm = load_llm().bind_tools(ticket_write_tools)

def ticket_logger_node(state: AgentState) -> dict:
    log.info("Agent entered node: ticket_logger_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(TICKET_WRITE_MANAGER_PROMPT, state))
    response = ticket_write_llm.invoke([sys_msg] + state.messages)  # Lookup tools only; mutation is deterministic after confirmation.
    log.debug(f"ticket_logger_node response: {response}")
    
    # Check if the LLM decided the draft is ready by calling the TicketDraft tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        draft_call = next((tc for tc in response.tool_calls if tc["name"] == "TicketDraft"), None)
        if draft_call:
            draft = TicketDraft(**draft_call["args"])
            return {
                "messages": [
                    AIMessage(content=_ticket_confirmation_summary(draft))
                ],
                "current_branch": "TICKET_WRITE_MANAGER",
                "pending_ticket_draft": draft,
                "awaiting_ticket_confirmation": True,
                "ticket_confirmation_decision": None,
                **_step_update(state, "TICKET_WRITE_MANAGER"),
            }

    # Otherwise it's either asking a clarifying question or calling a normal lookup tool
    return {
        "messages": [response],
        "current_branch": "TICKET_WRITE_MANAGER",
        **_step_update(state, "TICKET_WRITE_MANAGER"),
    }


def _ticket_confirmation_summary(draft: TicketDraft) -> str:
    operation = "Create" if draft.operation == "CREATE" else "Update"
    lines = [
        "Please review the details of the support ticket that will be raised below:\n",
        f"**Operation**: {operation}",
        f"**Ticket ID**: {draft.ticket_id or 'New'}",
        f"**System ID**: {draft.system_id or 'Not provided'}",
        f"**Employee ID**: {draft.employee_id or 'Not provided'}",
        f"**Title**: {draft.title or 'Not provided'}",
        f"**Description**: {draft.description or 'Not provided'}",
        f"**Category**: {draft.category or 'Not provided'}",
        f"**Status**: {draft.status or 'Not provided'}",
        f"**Ticket Type**: {draft.ticket_type or 'Not provided'}",
        f"**Priority**: {draft.priority or 'Automatic'}",
        "",
        "Should I proceed with this action? Please answer **yes** or **no**."
    ]
    return "  \n".join(lines)


triage_llm = load_llm()  # No tools bound — it can only think and respond
structured_triage_llm = triage_llm.with_structured_output(TriageDecision)

def _prompt_with_routing_context(prompt: str, state: AgentState) -> str:
    sections = [prompt]
    if state.routing_reason:
        sections.append(
            "Internal triage context (do not quote directly to the user):\n"
            f"{state.routing_reason}"
        )
    if state.infrastructure_context:
        context_lines = [
            "Patliputra-Corp infrastructure context was confirmed before this manager ran:",
        ]
        for system in state.infrastructure_context:
            context_lines.append(
                f"- ID: {system.id}; Name: {system.name}; Status: {system.status}; "
                f"Description: {system.description or 'Not provided'}; "
                f"Last checked: {system.last_checked or 'Not provided'}"
            )
        context_lines.append(
            "Use this confirmed context as the boundary for your answer. "
            "Do not provide generic guidance for unsupported services."
        )
        sections.append("\n".join(context_lines))
    return "\n\n".join(sections)

def triage_node(state: AgentState) -> dict:
    """Classifies the user's intent. No tools — just reasoning."""
    log.info("Agent entered node: triage_node")
    sys_msg = SystemMessage(content=_prompt_with_routing_context(TRIAGE_MANAGER_PROMPT, state))
    user_request = _latest_human_request(state)
    decision = cast(
        TriageDecision,
        structured_triage_llm.invoke([sys_msg] + state.messages),
    )
    if decision.next_node == "TICKET_ACTION_REQUEST" and _is_guidance_request(user_request):
        decision = decision.model_copy(
            update={
                "next_node": "INFRASTRUCTURE_LOOKUP_REQUEST",
                "routing_reason": "The user is asking for procedural guidance, so gather system context before the KB step.",
            }
        )
    log.info(f"Triage routed to: {decision.next_node}; reason: {decision.routing_reason}")
    return {
        "next_node": decision.next_node,
        "routing_reason": decision.routing_reason,
        **_step_update(state, "TRIAGE_MANAGER"),
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
    if hasattr(tool, "name") and tool.name not in tool_names:
        all_tools.append(tool)
        tool_names.add(tool.name)


def infrastructure_context_check_node(state: AgentState) -> dict:
    """Resolve the user's request against Patliputra-Corp's system catalog.

    This is a deterministic graph gate. It must run before triage and must not
    call an LLM or a LangChain tool.
    """
    if state.awaiting_ticket_confirmation:
        return {
            "infrastructure_context_status": "CONFIRMATION_PENDING",
            **_step_update(state, "INFRASTRUCTURE_CONTEXT_CHECK", reset=True),
        }

    # CONTEXT LOCK: If we are already in a conversation branch and have a system context, lock it in.
    if state.infrastructure_context_status == "FOUND" and state.current_branch:
        log.info("Context Lock engaged: Bypassing search to preserve existing context.")
        return {
            "infrastructure_context_status": "FOUND",
            **_step_update(state, "INFRASTRUCTURE_CONTEXT_CHECK", reset=True),
        }

    request = _latest_human_request(state)
    matches = system_repository.search_supported_systems_from_request(request)
    
    if len(matches) > 1:
        log.info("Ambiguous matches ({}). Engaging LLM keyword extraction fallback to find the best match.", len(matches))
        from ops_pilot.utils.large_language_models import load_llm
        llm = load_llm()
        prompt = INFRASTRUCTURE_KEYWORD_EXTRACTION_PROMPT.format(request=request)
        refined_keywords = llm.invoke(prompt).content
        log.info("LLM refined keywords: {}", refined_keywords)
        matches = system_repository.search_supported_systems_from_request(refined_keywords)

    if not matches:
        context_status = "NOT_FOUND"
    elif len(matches) == 1:
        context_status = "FOUND"
    elif len(matches) <= 3:
        context_status = "AMBIGUOUS"
    else:
        # Even after LLM refinement, it matched too many systems. Treat as not found.
        context_status = "NOT_FOUND"

    log.info(
        "Infrastructure context check: status={} candidates={} ids={}",
        context_status,
        len(matches),
        [system.id for system in matches],
    )
    return {
        "infrastructure_context_status": context_status,
        "infrastructure_context": matches,
        **_step_update(state, "INFRASTRUCTURE_CONTEXT_CHECK", reset=True),
    }


def out_of_scope_response_node(state: AgentState) -> dict:
    """Explain that the request does not map to Patliputra-Corp's catalog."""
    return {
        "messages": [
            AIMessage(
                content=(
                    "OpsPilot can help only with services, vendors, and systems "
                    "supported by Patliputra-Corp. I could not match this request "
                    "to a supported catalog entry. Please name the relevant "
                    "approved service, vendor, or system."
                )
            )
        ],
        **_step_update(state, "OUT_OF_SCOPE_RESPONSE"),
    }


def clarify_infrastructure_context_response_node(state: AgentState) -> dict:
    """Ask the user to choose between equally relevant catalog records."""
    choices = ", ".join(
        f"{system.name} ({system.id})" for system in state.infrastructure_context
    )
    return {
        "messages": [
            AIMessage(
                content=(
                    "I found more than one Patliputra-Corp service or vendor that "
                    f"could match this request: {choices}. Which one should I use?"
                )
            )
        ],
        **_step_update(state, "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE"),
    }


def ticket_confirmation_check_node(state: AgentState) -> dict:
    """Interpret confirmation without asking an LLM to reinterpret "yes"."""
    request = _latest_human_request(state).strip().lower()
    if re.fullmatch(r"(?:yes|y|confirm|confirmed|proceed|go ahead|do it)", request):
        decision = "CONFIRMED"
    elif re.fullmatch(r"(?:no|n|cancel|stop|do not|don't)", request):
        decision = "CANCELLED"
    else:
        decision = "UNCLEAR"
    return {
        "ticket_confirmation_decision": decision,
        **_step_update(state, "TICKET_CONFIRMATION_CHECK"),
    }


def cancel_pending_ticket_change_node(state: AgentState) -> dict:
    return {
        "messages": [
            AIMessage(content="No ticket change was made."),
        ],
        "pending_ticket_draft": None,
        "awaiting_ticket_confirmation": False,
        "ticket_confirmation_decision": "CANCELLED",
        "infrastructure_context_status": "FOUND",
        **_step_update(state, "CANCEL_PENDING_TICKET_CHANGE"),
    }


def clarify_ticket_confirmation_node(state: AgentState) -> dict:
    return {
        "messages": [
            AIMessage(
                content="Please answer yes to apply the prepared ticket action, or no to cancel it."
            ),
        ],
        "ticket_confirmation_decision": "UNCLEAR",
        **_step_update(state, "CLARIFY_TICKET_CONFIRMATION"),
    }


def apply_confirmed_ticket_change_node(state: AgentState) -> dict:
    """Apply the exact persisted draft once; do not reconstruct it with an LLM."""
    draft = state.pending_ticket_draft
    if draft is None:
        raise RuntimeError("Cannot confirm a ticket change without a pending draft")

    if draft.operation == "CREATE":
        required = {
            "employee_id": draft.employee_id,
            "title": draft.title,
            "description": draft.description,
            "status": draft.status,
            "category": draft.category,
            "ticket_type": draft.ticket_type,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Ticket draft is missing required create fields: "
                + ", ".join(missing)
            )
        payload = draft.model_dump(exclude_none=True)
        payload.pop("operation", None)
        result = create_ticket_tool.invoke(payload)
    else:
        if not draft.ticket_id:
            raise RuntimeError("Ticket update draft is missing ticket_id")
        payload = draft.model_dump(exclude_none=True)
        payload.pop("operation", None)
        result = update_ticket_tool.invoke(payload)

    if isinstance(result, str) and result.startswith(("Validation Error", "System Error")):
        return {
            "messages": [AIMessage(content="I could not apply that ticket action. Please review the details and try again.")],
            **_step_update(state, "APPLY_CONFIRMED_TICKET_CHANGE"),
        }

    if hasattr(result, "id"):
        ticket = result
        lines = [
            "✅ **Ticket action completed successfully.**\n",
            f"**Ticket ID**: {ticket.id}",
            f"**System ID**: {ticket.system_id}",
            f"**Employee ID**: {ticket.employee_id}",
            f"**Assigned To**: {ticket.assigned_to}",
            f"**Title**: {ticket.title}",
            f"**Description**: {ticket.description}",
            f"**Category**: {ticket.category}",
            f"**Status**: {ticket.status}",
            f"**Priority**: {ticket.priority}"
        ]
        msg = "  \n".join(lines)
    else:
        ticket_id = getattr(result, "id", draft.ticket_id or "the ticket")
        msg = f"✅ Ticket action completed successfully for {ticket_id}."

    return {
        "messages": [AIMessage(content=msg)],
        "pending_ticket_draft": None,
        "awaiting_ticket_confirmation": False,
        "ticket_confirmation_decision": "CONFIRMED",
        "infrastructure_context_status": "FOUND",
        **_step_update(state, "APPLY_CONFIRMED_TICKET_CHANGE"),
    }
