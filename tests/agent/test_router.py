import pytest
from ops_pilot.agent.state import AgentState
from ops_pilot.agent.router import (
    route_after_agent,
    route_after_infrastructure_context,
    route_after_ticket_confirmation_check,
    route_after_tools,
    triage_router,
)
from langchain_core.messages import AIMessage, ToolCall

def test_route_after_agent_with_tools():
    # Mock a ToolCall
    tool_call = ToolCall(name="dummy_tool", args={}, id="1")
    msg = AIMessage(content="", tool_calls=[tool_call])
    state = AgentState(messages=[msg])
    
    assert route_after_agent(state) == "TOOLS"

def test_route_after_agent_without_tools():
    msg = AIMessage(content="Hello")
    state = AgentState(messages=[msg])
    
    assert route_after_agent(state) == "DONE"

def test_route_after_tools():
    state = AgentState(current_branch="KNOWLEDGE_BASE_MANAGER")
    assert route_after_tools(state) == "KNOWLEDGE_BASE_MANAGER"


def test_route_after_tools_rejects_missing_branch():
    with pytest.raises(RuntimeError, match="valid current_branch"):
        route_after_tools(AgentState())

def test_triage_router():
    state = AgentState(next_node="INFRASTRUCTURE_LOOKUP_REQUEST")
    assert triage_router(state) == "INFRASTRUCTURE_MANAGER"
    
def test_triage_router_fallback():
    state = AgentState()
    with pytest.raises(RuntimeError, match="valid next_node"):
        triage_router(state)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("FOUND", "TRIAGE_MANAGER"),
        ("NOT_FOUND", "OUT_OF_SCOPE_RESPONSE"),
        ("AMBIGUOUS", "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE"),
    ],
)
def test_route_after_infrastructure_context(status, expected):
    state = AgentState(infrastructure_context_status=status)
    assert route_after_infrastructure_context(state) == expected


def test_route_after_infrastructure_context_rejects_missing_status():
    with pytest.raises(RuntimeError, match="missing or invalid"):
        route_after_infrastructure_context(AgentState())


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        ("CONFIRMED", "APPLY_CONFIRMED_TICKET_CHANGE"),
        ("CANCELLED", "CANCEL_PENDING_TICKET_CHANGE"),
        ("UNCLEAR", "CLARIFY_TICKET_CONFIRMATION"),
    ],
)
def test_route_after_ticket_confirmation_check(decision, expected):
    state = AgentState(ticket_confirmation_decision=decision)
    assert route_after_ticket_confirmation_check(state) == expected
