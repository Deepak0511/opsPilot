from ops_pilot.agent.state import AgentState
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from ops_pilot.utils.logger import log
from ops_pilot.agent.nodes import (
    triage_node, kb_node, infra_node, 
    ticket_read_node, ticket_logger_node,
    infrastructure_context_check_node,
    out_of_scope_response_node,
    clarify_infrastructure_context_response_node,
    ticket_confirmation_check_node,
    cancel_pending_ticket_change_node,
    clarify_ticket_confirmation_node,
    apply_confirmed_ticket_change_node,
    _step_update,
    all_tools,                          # combine all tool lists for the shared executor
)
from ops_pilot.agent.router import (
    triage_router,
    route_after_agent,
    route_after_tools,
    route_after_infrastructure_context,
    route_after_ticket_confirmation_check,
)
from ops_pilot.config.settings import lookup_for_setting
import sqlite3
# Shared tool executor — knows ALL tools, but each node's LLM
# can only REQUEST its own subset.
# Tool errors become ToolMessages so the calling agent can recover and respond.
tool_executor = ToolNode(all_tools, handle_tool_errors=True)


def tools_node(state: AgentState) -> dict:
    """Execute a requested tool and record the shared executor step."""
    updates = tool_executor.invoke(state)
    return {
        **updates,
        **_step_update(state, "TOOLS"),
    }

def create_agent():
    log.info("Compiling StateGraph for ops_pilot agent")
    graph = StateGraph(AgentState)

    ## Checkpointing setup.
    log.info(f"Connecting to checkpoint database at {lookup_for_setting['env_checkpoint_db_path']}")
    checkpoint_connection = sqlite3.connect(
    lookup_for_setting["env_checkpoint_db_path"],
    check_same_thread=False,
    )
    checkpoint_saver = SqliteSaver(
        checkpoint_connection,
        serde=JsonPlusSerializer(
            allowed_msgpack_modules=[
                ("ops_pilot.models.system", "System"),
                ("ops_pilot.agent.state", "TicketDraft"),
            ]
        ),
    )
    # ── Register nodes ──
    graph.add_node("TRIAGE_MANAGER", triage_node)
    graph.add_node("KNOWLEDGE_BASE_MANAGER", kb_node)
    graph.add_node("INFRASTRUCTURE_MANAGER", infra_node)
    graph.add_node("TICKET_READ_MANAGER", ticket_read_node)
    graph.add_node("TICKET_WRITE_MANAGER", ticket_logger_node)
    graph.add_node("TOOLS", tools_node)
    graph.add_node("INFRASTRUCTURE_CONTEXT_CHECK", infrastructure_context_check_node)
    graph.add_node("OUT_OF_SCOPE_RESPONSE", out_of_scope_response_node)
    graph.add_node(
        "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE",
        clarify_infrastructure_context_response_node,
    )
    graph.add_node("TICKET_CONFIRMATION_CHECK", ticket_confirmation_check_node)
    graph.add_node(
        "CANCEL_PENDING_TICKET_CHANGE",
        cancel_pending_ticket_change_node,
    )
    graph.add_node("CLARIFY_TICKET_CONFIRMATION", clarify_ticket_confirmation_node)
    graph.add_node(
        "APPLY_CONFIRMED_TICKET_CHANGE",
        apply_confirmed_ticket_change_node,
    )

    # ── Entry ──
    graph.add_edge(START, "INFRASTRUCTURE_CONTEXT_CHECK")
    graph.add_conditional_edges(
        "INFRASTRUCTURE_CONTEXT_CHECK",
        route_after_infrastructure_context,
        {
            "TRIAGE_MANAGER": "TRIAGE_MANAGER",
            "OUT_OF_SCOPE_RESPONSE": "OUT_OF_SCOPE_RESPONSE",
            "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE": "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE",
            "TICKET_CONFIRMATION_CHECK": "TICKET_CONFIRMATION_CHECK",
        },
    )
    graph.add_edge("OUT_OF_SCOPE_RESPONSE", END)
    graph.add_edge("CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE", END)
    graph.add_conditional_edges(
        "TICKET_CONFIRMATION_CHECK",
        route_after_ticket_confirmation_check,
        {
            "APPLY_CONFIRMED_TICKET_CHANGE": "APPLY_CONFIRMED_TICKET_CHANGE",
            "CANCEL_PENDING_TICKET_CHANGE": "CANCEL_PENDING_TICKET_CHANGE",
            "CLARIFY_TICKET_CONFIRMATION": "CLARIFY_TICKET_CONFIRMATION",
        },
    )
    graph.add_edge("APPLY_CONFIRMED_TICKET_CHANGE", END)
    graph.add_edge("CANCEL_PENDING_TICKET_CHANGE", END)
    graph.add_edge("CLARIFY_TICKET_CONFIRMATION", END)

    
    # ── Triage routes to specialized nodes ──
    graph.add_conditional_edges("TRIAGE_MANAGER", triage_router, {
        "INFRASTRUCTURE_MANAGER": "INFRASTRUCTURE_MANAGER",
        "KNOWLEDGE_BASE_MANAGER": "KNOWLEDGE_BASE_MANAGER",
        "TICKET_READ_MANAGER": "TICKET_READ_MANAGER",
        "TICKET_WRITE_MANAGER": "TICKET_WRITE_MANAGER",
    })

    # ── Each specialized node checks if it needs tools ──
    # If the LLM requested a tool, go to "tools". If it gave a final answer, go to END.
    for manager_name  in ["INFRASTRUCTURE_MANAGER", "KNOWLEDGE_BASE_MANAGER", "TICKET_READ_MANAGER", "TICKET_WRITE_MANAGER"]:
        graph.add_conditional_edges(
            manager_name , 
            route_after_agent,
            {
                "TOOLS": "TOOLS",
                "DONE": END,
            }
        )

    # ── After tools execute, go back to the node that called them ──
    # This creates the ReAct loop: Node -> Tools -> Node -> Tools -> Node -> END
    graph.add_conditional_edges(
        "TOOLS",
        route_after_tools,
        {
            "INFRASTRUCTURE_MANAGER": "INFRASTRUCTURE_MANAGER",
            "KNOWLEDGE_BASE_MANAGER": "KNOWLEDGE_BASE_MANAGER",
            "TICKET_READ_MANAGER": "TICKET_READ_MANAGER",
            "TICKET_WRITE_MANAGER": "TICKET_WRITE_MANAGER",
        },
    )

    return graph.compile(checkpointer=checkpoint_saver)
