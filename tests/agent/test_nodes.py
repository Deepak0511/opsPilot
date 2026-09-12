import pytest
from ops_pilot.agent.state import AgentState, TriageDecision
from langchain_core.messages import HumanMessage, AIMessage

def test_triage_node(mocker):
    # We need to mock structured_triage_llm
    mock_triage_decision = TriageDecision(next_node="kb_node")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    mock_llm.invoke.return_value = mock_triage_decision
    
    from ops_pilot.agent.nodes import triage_node
    
    state = AgentState(messages=[HumanMessage(content="How do I reset my password?")])
    result = triage_node(state)
    
    assert result == {"next_node": "kb_node"}
    mock_llm.invoke.assert_called_once()

def test_kb_node(mocker):
    mock_msg = AIMessage(content="Here is a KB article")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.kb_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import kb_node
    
    state = AgentState(messages=[HumanMessage(content="Search for password reset")])
    result = kb_node(state)
    
    assert result["current_branch"] == "kb_node"
    assert result["messages"][0].content == "Here is a KB article"

def test_infra_node(mocker):
    mock_msg = AIMessage(content="System is online")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.infra_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import infra_node
    
    state = AgentState(messages=[HumanMessage(content="Is the DB up?")])
    result = infra_node(state)
    
    assert result["current_branch"] == "infra_node"
    assert result["messages"][0].content == "System is online"

def test_ticket_read_node(mocker):
    mock_msg = AIMessage(content="Ticket is open")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.ticket_read_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import ticket_read_node
    
    state = AgentState(messages=[HumanMessage(content="Status of INC-001?")])
    result = ticket_read_node(state)
    
    assert result["current_branch"] == "ticket_read_node"

def test_ticket_logger_node(mocker):
    mock_msg = AIMessage(content="Created ticket INC-002")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.ticket_write_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import ticket_logger_node
    
    state = AgentState(messages=[HumanMessage(content="Create a ticket for broken laptop")])
    result = ticket_logger_node(state)
    
    assert result["current_branch"] == "ticket_logger_node"
