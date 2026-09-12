from ops_pilot.agent.state import AgentState
from ops_pilot.utils.logger import log

def route_after_agent(state: AgentState) -> str:
    """Check if the LLM requested a tool call. If so, route to 'tools', else 'done'."""
    last_message = state.messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        log.info("Agent requested tools; routing to 'tools'")
        return "tools"
    log.info("Agent finished; routing to 'done'")
    return "done"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to whichever node invoked them."""
    return state.current_branch


# Router: reads the triage result and routes deterministically
def triage_router(state: AgentState) -> str:
    """Routes to the correct specialized node based on triage structured output."""
    if state.next_node:
        log.info(f"Triage routed to next_node: {state.next_node}")
        return state.next_node
    log.warning("Triage did not provide next_node; defaulting to kb_node")
    return "kb_node"  # Safe fallback