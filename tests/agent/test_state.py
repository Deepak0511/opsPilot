import pytest
from ops_pilot.agent.state import AgentState, TriageDecision
from langchain_core.messages import HumanMessage

def test_agent_state_initialization():
    state = AgentState()
    assert state.messages == []
    assert state.current_branch is None
    assert state.next_node is None
    assert state.infrastructure_context_status is None
    assert state.infrastructure_context == []

def test_agent_state_with_messages():
    msg = HumanMessage(content="Hello")
    state = AgentState(messages=[msg])
    assert len(state.messages) == 1
    assert state.messages[0].content == "Hello"

def test_triage_decision_validation():
    # Valid
    decision = TriageDecision(
        next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
        routing_reason="The request is a knowledge-base question.",
    )
    assert decision.next_node == "KNOWLEDGE_BASE_LOOKUP_REQUEST"
    assert decision.routing_reason == "The request is a knowledge-base question."
    
    # Invalid
    with pytest.raises(Exception):
        TriageDecision(next_node="invalid_node")
