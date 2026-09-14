from ops_pilot.agent.state import AgentState
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from ops_pilot.utils.logger import log
from ops_pilot.agent.nodes import (
    supervisor_node, kb_node, infra_node, 
    ticket_read_node, ticket_logger_node,
    all_tools,                          # combine all tool lists for the shared executor
)
from ops_pilot.agent.router import supervisor_router, route_after_agent, route_after_tools
from ops_pilot.config.settings import lookup_for_setting
import sqlite3
# Shared tool executor — knows ALL tools, but each node's LLM
# can only REQUEST its own subset.
# Tool errors become ToolMessages so the calling agent can recover and respond.
tool_executor = ToolNode(all_tools, handle_tool_errors=True)

def create_agent():
    log.info("Compiling StateGraph for ops_pilot agent")
    graph = StateGraph(AgentState)

    ## Checkpointing setup.
    log.info(f"Connecting to checkpoint database at {lookup_for_setting['env_checkpoint_db_path']}")
    checkpoint_connection = sqlite3.connect(
    lookup_for_setting["env_checkpoint_db_path"],
    check_same_thread=False,
    )
    checkpoint_saver = SqliteSaver(checkpoint_connection)
    # ── Register nodes ──
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("kb_node", kb_node)
    graph.add_node("infra_node", infra_node)
    graph.add_node("ticket_read_node", ticket_read_node)
    graph.add_node("ticket_logger_node", ticket_logger_node)
    graph.add_node("tools", tool_executor)

    # ── Entry ──
    graph.add_edge(START, "supervisor")

    # ── Supervisor routes to specialized nodes ──
    graph.add_conditional_edges("supervisor", supervisor_router, {
        "kb_node": "kb_node",
        "infra_node": "infra_node",
        "ticket_read_node": "ticket_read_node",
        "ticket_logger_node": "ticket_logger_node",
        "__end__": END,
    })

    # ── Each specialized node checks if it needs tools ──
    # If the LLM requested a tool, go to "tools". If it gave a final answer, return to supervisor or END.
    for node_name in ["kb_node", "infra_node", "ticket_read_node", "ticket_logger_node"]:
        graph.add_conditional_edges(
            node_name, 
            route_after_agent, 
            {"tools": "tools", "supervisor": "supervisor", "__end__": END}
        )

    # ── After tools execute, go back to the node that called them ──
    # This creates the ReAct loop: Node -> Tools -> Node -> Tools -> Node -> END
    graph.add_conditional_edges("tools", route_after_tools)

    return graph.compile(checkpointer=checkpoint_saver)
