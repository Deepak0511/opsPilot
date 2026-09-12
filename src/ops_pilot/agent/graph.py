from ops_pilot.agent.state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from ops_pilot.agent.nodes import (
    triage_node, kb_node, infra_node, 
    ticket_read_node, ticket_logger_node,
    all_tools,                          # combine all tool lists for the shared executor
)
from ops_pilot.agent.router import triage_router, route_after_agent, route_after_tools

# Shared tool executor — knows ALL tools, but each node's LLM
# can only REQUEST its own subset. Think of it as a single 
# DispatcherServlet that can route to any @Controller.
tool_executor = ToolNode(all_tools)

def create_agent():
    graph = StateGraph(AgentState)

    # ── Register nodes ──
    graph.add_node("triage", triage_node)
    graph.add_node("kb_node", kb_node)
    graph.add_node("infra_node", infra_node)
    graph.add_node("ticket_read_node", ticket_read_node)
    graph.add_node("ticket_logger_node", ticket_logger_node)
    graph.add_node("tools", tool_executor)

    # ── Entry ──
    graph.add_edge(START, "triage")

    # ── Triage routes to specialized nodes ──
    graph.add_conditional_edges("triage", triage_router, {
        "kb_node": "kb_node",
        "infra_node": "infra_node",
        "ticket_read_node": "ticket_read_node",
        "ticket_logger_node": "ticket_logger_node",
    })

    # ── Each specialized node checks if it needs tools ──
    # If the LLM requested a tool, go to "tools". If it gave a final answer, go to END.
    for node_name in ["kb_node", "infra_node", "ticket_read_node", "ticket_logger_node"]:
        graph.add_conditional_edges(
            node_name, 
            route_after_agent, 
            {"tools": "tools", "done": END}
        )

    # ── After tools execute, go back to the node that called them ──
    # This creates the ReAct loop: Node -> Tools -> Node -> Tools -> Node -> END
    graph.add_conditional_edges("tools", route_after_tools)

    return graph.compile()
