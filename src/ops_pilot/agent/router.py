from ops_pilot.agent.state import AgentState
from ops_pilot.utils.logger import log

def route_after_agent(state: AgentState) -> str:
    """Check if the LLM requested a tool call or needs to pause for human input."""
    if state.requires_human_input:
        log.info("Agent requires human input; routing to __end__")
        return "__end__"
        
    last_message = state.messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        log.info("Agent requested tools; routing to 'tools'")
        return "tools"
    
    log.info("Agent finished; routing back to supervisor")
    return "supervisor"


def route_after_tools(state: AgentState) -> str:
    """After tools execute, route back to whichever node invoked them."""
    return state.current_branch


def supervisor_router(state: AgentState) -> str:
    """Routes to the correct specialized node based on supervisor structured output."""
    if state.next_node:
        if state.next_node == "FINISH":
            log.info("Supervisor routed to FINISH")
            return "__end__"
        log.info(f"Supervisor routed to next_node: {state.next_node}")
        return state.next_node
    log.warning("Supervisor did not provide next_node; defaulting to kb_node")
    return "kb_node"  # Safe fallback