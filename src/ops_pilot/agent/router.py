from ops_pilot.agent.state import AgentState
from ops_pilot.utils.logger import log
from langchain_core.messages import AIMessage


# Router: reads the triage result and routes deterministically
def triage_router(state: AgentState) -> str:
    """Routes to the correct specialized node based on triage structured output."""
    if state.next_node:
        if state.next_node in {"KNOWLEDGE_BASE_LOOKUP_REQUEST", "TICKET_ACTION_REQUEST"}:
            log.info(
                f"Triage selected {state.next_node}; routing through INFRASTRUCTURE_MANAGER  first"
            )# TODO: For removal-This is a temporary workaround until we can get the LLM to output the correct node directly.
            return "INFRASTRUCTURE_LOOKUP_REQUEST"
        log.info(f"Triage routed to next_node: {state.next_node}")
        return state.next_node
    log.warning("Triage did not provide next_node; defaulting to INFRASTRUCTURE_LOOKUP_REQUEST")
    return "INFRASTRUCTURE_LOOKUP_REQUEST"  # Safe fallback: gather system context before KB or ticket work

def route_after_agent(state: AgentState) -> str:
    """Check if the LLM requested a tool call. If so, route to 'TOOLS', else 'done'."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        log.info("Agent requested TOOLS; routing to 'TOOLS'")
        return "TOOLS"
    if state.current_branch == "INFRASTRUCTURE_MANAGER":
        if state.next_node == "KNOWLEDGE_BASE_LOOKUP_REQUEST":
            log.info("Infrastructure context gathered; routing to KNOWLEDGE_BASE_MANAGER.")
            return "KNOWLEDGE_BASE_MANAGER"

        if state.next_node == "TICKET_LOOKUP_REQUEST":
            log.info("Infrastructure context gathered; routing to TICKET_READ_MANAGER.")
            return "TICKET_READ_MANAGER"

        if state.next_node == "TICKET_ACTION_REQUEST":
            log.info("Infrastructure context gathered; routing to TICKET_WRITE_MANAGER.")
            return "TICKET_WRITE_MANAGER"

        # Same existing fallback: infrastructure proceeds to KB.
        log.info("Infrastructure context gathered; routing to KNOWLEDGE_BASE_MANAGER.")
        return "KNOWLEDGE_BASE_MANAGER"

    log.info("Agent finished; routing to DONE.")
    return "DONE"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to whichever node invoked them."""
    branch = state.current_branch
    if branch is None:
        return "INFRASTRUCTURE_MANAGER" #TODO: Review if it is causing endless loop.
    return branch


