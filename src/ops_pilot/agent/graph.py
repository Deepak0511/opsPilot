from ops_pilot.agent.state import AgentState
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from ops_pilot.utils.logger import log
from ops_pilot.agent.nodes import (
    triage_node, kb_node, infra_node, 
    ticket_read_node, ticket_logger_node,
    all_tools,                          # combine all tool lists for the shared executor
)
from ops_pilot.agent.router import triage_router, route_after_agent, route_after_tools
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
    graph.add_node("TRIAGE_MANAGER", triage_node)
    graph.add_node("KNOWLEDGE_BASE_MANAGER", kb_node)
    graph.add_node("INFRASTRUCTURE_MANAGER", infra_node)
    graph.add_node("TICKET_READ_MANAGER", ticket_read_node)
    graph.add_node("TICKET_WRITE_MANAGER", ticket_logger_node)
    graph.add_node("TOOLS", tool_executor)

    # ── Entry ──
    graph.add_edge(START, "TRIAGE_MANAGER")

    
    # ── Triage routes to specialized nodes ──
    graph.add_conditional_edges("TRIAGE_MANAGER", triage_router, {
        "INFRASTRUCTURE_LOOKUP_REQUEST": "INFRASTRUCTURE_MANAGER",
        "KNOWLEDGE_BASE_LOOKUP_REQUEST": "KNOWLEDGE_BASE_MANAGER",
        "TICKET_LOOKUP_REQUEST": "TICKET_READ_MANAGER",
        "TICKET_ACTION_REQUEST": "TICKET_WRITE_MANAGER",
    })

    # ── Each specialized node checks if it needs tools ──
    # If the LLM requested a tool, go to "tools". If it gave a final answer, go to END.
    for manager_name  in ["INFRASTRUCTURE_MANAGER", "KNOWLEDGE_BASE_MANAGER", "TICKET_READ_MANAGER", "TICKET_WRITE_MANAGER"]:
        graph.add_conditional_edges(
            manager_name , 
            route_after_agent,
            {
                "TOOLS": "TOOLS",
                "KNOWLEDGE_BASE_MANAGER": "KNOWLEDGE_BASE_MANAGER",
                "TICKET_READ_MANAGER": "TICKET_READ_MANAGER",
                "TICKET_WRITE_MANAGER": "TICKET_WRITE_MANAGER",
                "DONE": END,
            }
        )

    # ── After tools execute, go back to the node that called them ──
    # This creates the ReAct loop: Node -> Tools -> Node -> Tools -> Node -> END
    graph.add_conditional_edges("TOOLS", route_after_tools)

    return graph.compile(checkpointer=checkpoint_saver)
