import pytest
from ops_pilot.agent.state import AgentState, TriageDecision
from langchain_core.messages import HumanMessage, AIMessage
from ops_pilot.prompts.system_prompt import TRIAGE_MANAGER_PROMPT, TICKET_WRITE_MANAGER_PROMPT

def test_triage_node(mocker):
    # We need to mock structured_triage_llm
    mock_triage_decision = TriageDecision(
        next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
        routing_reason="The user is asking for password reset instructions.",
    )
    mock_llm = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    mock_llm.invoke.return_value = mock_triage_decision
    
    from ops_pilot.agent.nodes import triage_node
    
    state = AgentState(messages=[HumanMessage(content="How do I reset my password?")])
    result = triage_node(state)
    
    assert result == {
        "next_node": "KNOWLEDGE_BASE_LOOKUP_REQUEST",
        "routing_reason": "The user is asking for password reset instructions.",
        "completed_steps": ["TRIAGE_MANAGER"],
        "execution_count": 1,
    }
    mock_llm.invoke.assert_called_once()


def test_triage_node_keeps_how_to_request_out_of_ticket_logger(mocker):
    mock_llm = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    mock_llm.invoke.return_value = TriageDecision(
        next_node="TICKET_ACTION_REQUEST",
        routing_reason="The user needs a reimbursement ticket.",
    )

    from ops_pilot.agent.nodes import triage_node

    result = triage_node(
        AgentState(
            messages=[
                HumanMessage(
                    content="How can I raise a reimbursement request for my internet bill?"
                )
            ]
        )
    )

    assert result["next_node"] == "INFRASTRUCTURE_LOOKUP_REQUEST"
    assert "procedural guidance" in result["routing_reason"]


def test_triage_node_receives_confirmed_infrastructure_context(mocker):
    mock_llm = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    mock_llm.invoke.return_value = TriageDecision(
        next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
        routing_reason="The request is a supported VPN procedure.",
    )
    from ops_pilot.agent.nodes import triage_node
    from ops_pilot.models.system import System

    triage_node(
        AgentState(
            messages=[HumanMessage(content="How do I connect to VPN?")],
            infrastructure_context_status="FOUND",
            infrastructure_context=[
                System(
                    id="SYS-VPN",
                    name="Patliputra VPN",
                    status="Operational",
                    description="Approved VPN",
                )
            ],
        )
    )

    prompt = mock_llm.invoke.call_args.args[0][0].content
    assert "Patliputra-Corp infrastructure context" in prompt
    assert "SYS-VPN" in prompt
    assert "Patliputra VPN" in prompt


def test_triage_prompt_distinguishes_guidance_from_ticket_action():
    assert "How can I" in TRIAGE_MANAGER_PROMPT
    assert "never directly to 'TICKET_ACTION_REQUEST'" in TRIAGE_MANAGER_PROMPT
    assert "Create a reimbursement ticket" in TRIAGE_MANAGER_PROMPT
    assert "Do not use it to answer" in TICKET_WRITE_MANAGER_PROMPT

def test_kb_node(mocker):
    mock_msg = AIMessage(content="Here is a KB article")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.kb_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import kb_node
    
    state = AgentState(messages=[HumanMessage(content="Search for password reset")])
    result = kb_node(state)
    
    assert result["current_branch"] == "KNOWLEDGE_BASE_MANAGER"
    assert result["messages"][0].content == "Here is a KB article"


def test_kb_node_receives_confirmed_infrastructure_context(mocker):
    mock_llm = mocker.patch("ops_pilot.agent.nodes.kb_llm")
    mock_llm.invoke.return_value = AIMessage(content="VPN steps")
    from ops_pilot.agent.nodes import kb_node
    from ops_pilot.models.system import System

    kb_node(
        AgentState(
            messages=[HumanMessage(content="How do I connect to VPN?")],
            infrastructure_context=[
                System(
                    id="SYS-VPN",
                    name="Patliputra VPN",
                    status="Operational",
                    description="Approved VPN",
                )
            ],
        )
    )

    prompt = mock_llm.invoke.call_args.args[0][0].content
    assert "SYS-VPN" in prompt
    assert "Do not provide generic guidance" in prompt

def test_infra_node(mocker):
    mock_msg = AIMessage(content="System is online")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.infra_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import infra_node
    
    state = AgentState(messages=[HumanMessage(content="Is the DB up?")])
    result = infra_node(state)
    
    assert result["current_branch"] == "INFRASTRUCTURE_MANAGER"
    assert result["messages"][0].content == "System is online"

def test_ticket_read_node(mocker):
    mock_msg = AIMessage(content="Ticket is open")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.ticket_read_llm")
    mock_llm.invoke.return_value = mock_msg
    
    from ops_pilot.agent.nodes import ticket_read_node
    
    state = AgentState(messages=[HumanMessage(content="Status of INC-001?")])
    result = ticket_read_node(state)
    
    assert result["current_branch"] == "TICKET_READ_MANAGER"

def test_ticket_logger_node(mocker):
    mock_msg = AIMessage(content="Created ticket INC-002")
    mock_llm = mocker.patch("ops_pilot.agent.nodes.ticket_write_llm")
    mock_llm.invoke.return_value = mock_msg
    draft_llm = mocker.patch("ops_pilot.agent.nodes.ticket_draft_llm")
    from ops_pilot.agent.state import TicketDraft
    draft_llm.invoke.return_value = TicketDraft(
        operation="CREATE",
        employee_id="E001",
        title="Broken laptop",
        description="Laptop is broken",
        status="Open",
        category="Hardware",
        ticket_type="INC",
        system_id="SYS-HW",
    )
    
    from ops_pilot.agent.nodes import ticket_logger_node
    
    state = AgentState(messages=[HumanMessage(content="Create a ticket for broken laptop")])
    result = ticket_logger_node(state)

    assert result["current_branch"] == "TICKET_WRITE_MANAGER"
    assert result["awaiting_ticket_confirmation"] is True
    assert result["pending_ticket_draft"].operation == "CREATE"
    assert "Should I proceed?" in result["messages"][0].content


def test_infrastructure_context_check_uses_full_latest_user_request(mocker):
    mock_search = mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request"
    )
    from ops_pilot.models.system import System

    mock_search.return_value = [
        System(
            id="SYS-VPN",
            name="Patliputra VPN",
            status="Operational",
            description="Approved VPN",
        )
    ]

    from ops_pilot.agent.nodes import infrastructure_context_check_node

    result = infrastructure_context_check_node(
        AgentState(
            messages=[
                HumanMessage(content="Earlier request"),
                AIMessage(content="Earlier answer"),
                HumanMessage(content="How do I reset my VPN password?"),
            ],
            next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
            current_branch="KNOWLEDGE_BASE_MANAGER",
        )
    )

    assert result["infrastructure_context_status"] == "FOUND"
    assert result["infrastructure_context"][0].id == "SYS-VPN"
    assert mock_search.call_args.args == ("How do I reset my VPN password?",)


def test_infrastructure_context_check_marks_ambiguous_without_selecting(mocker):
    from ops_pilot.models.system import System

    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[
            System(id="SYS-A", name="Acme Internet", status="Online"),
            System(id="SYS-B", name="Bharat Internet", status="Online"),
        ],
    )
    from ops_pilot.agent.nodes import infrastructure_context_check_node

    result = infrastructure_context_check_node(
        AgentState(messages=[HumanMessage(content="internet reimbursement")])
    )

    assert result["infrastructure_context_status"] == "AMBIGUOUS"
    assert len(result["infrastructure_context"]) == 2


def test_out_of_scope_response_is_terminal_message():
    from ops_pilot.agent.nodes import out_of_scope_response_node

    result = out_of_scope_response_node(AgentState())
    assert "supported by Patliputra-Corp" in result["messages"][0].content
    assert "not onboarded" not in result["messages"][0].content.lower()


def test_ambiguous_context_response_lists_catalog_choices():
    from ops_pilot.agent.nodes import clarify_infrastructure_context_response_node
    from ops_pilot.models.system import System

    result = clarify_infrastructure_context_response_node(
        AgentState(
            infrastructure_context=[
                System(id="SYS-A", name="Acme Internet", status="Online"),
                System(id="SYS-B", name="Bharat Internet", status="Online"),
            ]
        )
    )
    content = result["messages"][0].content
    assert "Acme Internet (SYS-A)" in content
    assert "Bharat Internet (SYS-B)" in content


def test_step_guard_rejects_execution_beyond_limit():
    from ops_pilot.agent.nodes import MAX_EXECUTION_STEPS, _step_update

    with pytest.raises(RuntimeError, match="maximum execution steps"):
        _step_update(
            AgentState(
                execution_count=MAX_EXECUTION_STEPS,
                completed_steps=["TOOLS"],
            ),
            "KNOWLEDGE_BASE_MANAGER",
        )


def test_context_entry_resets_step_budget_for_a_new_turn(mocker):
    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[],
    )
    from ops_pilot.agent.nodes import infrastructure_context_check_node

    result = infrastructure_context_check_node(
        AgentState(
            messages=[HumanMessage(content="A new user turn")],
            completed_steps=["OUT_OF_SCOPE_RESPONSE"] * 11,
            execution_count=11,
        )
    )

    assert result["completed_steps"] == ["INFRASTRUCTURE_CONTEXT_CHECK"]
    assert result["execution_count"] == 1


def test_ticket_confirmation_check_parses_yes_without_llm():
    from ops_pilot.agent.nodes import ticket_confirmation_check_node
    from ops_pilot.agent.state import TicketDraft

    result = ticket_confirmation_check_node(
        AgentState(
            messages=[HumanMessage(content="yes")],
            awaiting_ticket_confirmation=True,
            pending_ticket_draft=TicketDraft(operation="CREATE"),
        )
    )

    assert result["ticket_confirmation_decision"] == "CONFIRMED"


def test_ticket_confirmation_check_parses_no_and_unclear():
    from ops_pilot.agent.nodes import ticket_confirmation_check_node
    from ops_pilot.agent.state import TicketDraft

    base = AgentState(
        awaiting_ticket_confirmation=True,
        pending_ticket_draft=TicketDraft(operation="CREATE"),
    )
    assert ticket_confirmation_check_node(
        base.model_copy(update={"messages": [HumanMessage(content="no")]})
    )["ticket_confirmation_decision"] == "CANCELLED"
    assert ticket_confirmation_check_node(
        base.model_copy(update={"messages": [HumanMessage(content="maybe")]})
    )["ticket_confirmation_decision"] == "UNCLEAR"


def test_apply_confirmed_ticket_change_uses_persisted_draft_once(mocker):
    from ops_pilot.agent.nodes import apply_confirmed_ticket_change_node
    from ops_pilot.agent.state import TicketDraft
    from ops_pilot.models.ticket import Ticket
    from datetime import datetime

    create = mocker.patch("ops_pilot.agent.nodes.create_ticket_tool")
    create.invoke.return_value = Ticket(
        id="INC-100",
        employee_id="E001",
        title="VPN unavailable",
        description="VPN is unavailable",
        status="Open",
        priority="High",
        category="Network",
        system_id="SYS-VPN",
        assigned_to="IT001",
        created_date=datetime.now(),
        updated_date=datetime.now(),
    )
    draft = TicketDraft(
        operation="CREATE",
        employee_id="E001",
        title="VPN unavailable",
        description="VPN is unavailable",
        status="Open",
        category="Network",
        ticket_type="INC",
        system_id="SYS-VPN",
    )

    result = apply_confirmed_ticket_change_node(
        AgentState(
            pending_ticket_draft=draft,
            awaiting_ticket_confirmation=True,
            ticket_confirmation_decision="CONFIRMED",
        )
    )

    create.invoke.assert_called_once()
    assert result["pending_ticket_draft"] is None
    assert result["awaiting_ticket_confirmation"] is False
    assert "INC-100" in result["messages"][0].content
