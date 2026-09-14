from ops_pilot.agent.state import AgentState
from ops_pilot.utils.logger import log
from langchain_core.messages import AIMessage


def route_after_agent(state: AgentState) -> str:
    """Check if the LLM requested a tool call. If so, route to 'tools', else 'done'."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        log.info("Agent requested tools; routing to 'tools'")
        return "tools"
    if state.current_branch == "infra_node":
        next_node = state.next_node
        if next_node in {"kb_node", "ticket_read_node", "ticket_logger_node"}:
            log.info(f"Infrastructure context gathered; routing to '{next_node}'")
            return next_node
        log.info("Infrastructure context gathered; routing to 'kb_node'")
        return "kb_node"
    log.info("Agent finished; routing to 'done'")
    return "done"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to whichever node invoked them."""
    branch = state.current_branch
    if branch is None:
        return "infra_node"
    return branch


# Router: reads the triage result and routes deterministically
def triage_router(state: AgentState) -> str:
    """Routes to the correct specialized node based on triage structured output."""
    if state.next_node:
        if state.next_node in {"kb_node", "ticket_logger_node"}:
            log.info(
                f"Triage selected {state.next_node}; routing through infra_node first"
            )
            return "infra_node"
        log.info(f"Triage routed to next_node: {state.next_node}")
        return state.next_node
    log.warning("Triage did not provide next_node; defaulting to infra_node")
    return "infra_node"  # Safe fallback: gather system context before KB or ticket work