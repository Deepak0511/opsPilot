import pytest
from ops_pilot.agent.state import AgentState
from ops_pilot.agent.router import route_after_agent, route_after_tools, triage_router
from langchain_core.messages import AIMessage, ToolCall

def test_route_after_agent_with_tools():
    # Mock a ToolCall
    tool_call = ToolCall(name="dummy_tool", args={}, id="1")
    msg = AIMessage(content="", tool_calls=[tool_call])
    state = AgentState(messages=[msg])
    
    assert route_after_agent(state) == "tools"

def test_route_after_agent_without_tools():
    msg = AIMessage(content="Hello")
    state = AgentState(messages=[msg])
    
    assert route_after_agent(state) == "done"

def test_route_after_tools():
    state = AgentState(current_branch="kb_node")
    assert route_after_tools(state) == "kb_node"

def test_triage_router():
    state = AgentState(next_node="infra_node")
    assert triage_router(state) == "infra_node"
    
def test_triage_router_fallback():
    state = AgentState()
    assert triage_router(state) == "kb_node"
