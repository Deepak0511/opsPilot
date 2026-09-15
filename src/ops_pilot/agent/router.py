from ops_pilot.agent.state import AgentState
from ops_pilot.utils.logger import log
from langchain_core.messages import AIMessage


def route_after_infrastructure_context(state: AgentState) -> str:
    """Route the deterministic catalog lookup outcome before triage."""
    routes = {
        "FOUND": "TRIAGE_MANAGER",
        "NOT_FOUND": "OUT_OF_SCOPE_RESPONSE",
        "AMBIGUOUS": "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE",
        "CONFIRMATION_PENDING": "TICKET_CONFIRMATION_CHECK",
    }
    status = state.infrastructure_context_status
    if status not in routes:
        raise RuntimeError(
            "Infrastructure context status is missing or invalid: "
            f"{status!r}"
        )
    return routes[status]


def route_after_ticket_confirmation_check(state: AgentState) -> str:
    routes = {
        "CONFIRMED": "APPLY_CONFIRMED_TICKET_CHANGE",
        "CANCELLED": "CANCEL_PENDING_TICKET_CHANGE",
        "UNCLEAR": "CLARIFY_TICKET_CONFIRMATION",
    }
    decision = state.ticket_confirmation_decision
    if decision not in routes:
        raise RuntimeError(
            "Ticket confirmation decision is missing or invalid: "
            f"{decision!r}"
        )
    return routes[decision]


# Router: reads the triage result and routes deterministically
def triage_router(state: AgentState) -> str:
    """Map the existing triage value directly to its manager graph node."""
    routes = {
        "INFRASTRUCTURE_LOOKUP_REQUEST": "INFRASTRUCTURE_MANAGER",
        "KNOWLEDGE_BASE_LOOKUP_REQUEST": "KNOWLEDGE_BASE_MANAGER",
        "TICKET_LOOKUP_REQUEST": "TICKET_READ_MANAGER",
        "TICKET_ACTION_REQUEST": "TICKET_WRITE_MANAGER",
    }
    if state.next_node not in routes:
        raise RuntimeError(
            "Triage did not provide a valid next_node: "
            f"{state.next_node!r}"
        )
    destination = routes[state.next_node]
    log.info("Triage routed {} to {}", state.next_node, destination)
    return destination

def route_after_agent(state: AgentState) -> str:
    """Check if the LLM requested a tool call. If so, route to 'TOOLS', else 'done'."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        log.info("Agent requested TOOLS; routing to 'TOOLS'")
        return "TOOLS"
    log.info("Agent finished; routing to DONE.")
    return "DONE"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to whichever node invoked them."""
    branch = state.current_branch
    valid_branches = {
        "INFRASTRUCTURE_MANAGER",
        "KNOWLEDGE_BASE_MANAGER",
        "TICKET_READ_MANAGER",
        "TICKET_WRITE_MANAGER",
    }
    if branch not in valid_branches:
        raise RuntimeError(
            "Tool execution has no valid current_branch: "
            f"{branch!r}"
        )
    return branch
