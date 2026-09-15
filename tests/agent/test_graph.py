import pytest
import uuid
from ops_pilot.agent.graph import create_agent
from ops_pilot.agent.router import triage_router
from ops_pilot.agent.router import route_after_agent
from ops_pilot.agent.state import TriageDecision, AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolCall


def test_triage_router_defaults_to_infra_node():
    state = AgentState(messages=[HumanMessage(content="Need help with a system issue")])
    with pytest.raises(RuntimeError, match="valid next_node"):
        triage_router(state)


def test_triage_router_sends_kb_directly_to_kb_manager():
    state = AgentState(
        messages=[HumanMessage(content="How do I raise a reimbursement request?")],
        next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
    )
    assert triage_router(state) == "KNOWLEDGE_BASE_MANAGER"


def test_infra_node_continues_to_kb_after_context_is_gathered():
    state = AgentState(
        messages=[AIMessage(content="System context gathered")],
        current_branch="INFRASTRUCTURE_MANAGER",
        next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
    )
    assert route_after_agent(state) == "DONE"


def test_infra_node_continues_to_ticket_logger_when_selected():
    state = AgentState(
        messages=[AIMessage(content="System context gathered")],
        current_branch="INFRASTRUCTURE_MANAGER",
        next_node="TICKET_ACTION_REQUEST",
    )
    assert route_after_agent(state) == "DONE"


def test_create_agent():
    # Calling create_agent compiles the graph.
    # We just want to ensure it compiles without errors
    # and has the expected nodes and edges.
    app = create_agent()
    
    assert app is not None
    
    # Check if expected nodes exist in the compiled graph's nodes mapping
    nodes = app.nodes.keys()
    expected_nodes = [
        "INFRASTRUCTURE_CONTEXT_CHECK",
        "OUT_OF_SCOPE_RESPONSE",
        "CLARIFY_INFRASTRUCTURE_CONTEXT_RESPONSE",
        "TRIAGE_MANAGER",
        "KNOWLEDGE_BASE_MANAGER",
        "INFRASTRUCTURE_MANAGER",
        "TICKET_READ_MANAGER",
        "TICKET_WRITE_MANAGER",
        "TOOLS"
    ]
    for n in expected_nodes:
        assert n in nodes

def test_graph_visualization():
    # Optional test: we can just check if get_graph() works
    app = create_agent()
    graph = app.get_graph()
    assert graph is not None
    # Just verifies that the structure is valid for mermaid generation
    try:
        mermaid = graph.draw_mermaid()
        assert isinstance(mermaid, str)
    except Exception as e:
        pytest.fail(f"Could not draw mermaid graph: {e}")

class MockTriageLLM:
    def invoke(self, *args, **kwargs):
        return TriageDecision(
            next_node="KNOWLEDGE_BASE_LOOKUP_REQUEST",
            routing_reason="The user is asking for VPN instructions.",
        )

class MockKBLLM:
    def __init__(self, tool_call):
        self.call_count = 0
        self.tool_call = tool_call
        
    def invoke(self, *args, **kwargs):
        if self.call_count == 0:
            self.call_count += 1
            return AIMessage(content="", tool_calls=[self.tool_call])
        return AIMessage(content="Here is how to connect to VPN...")

def test_graph_end_to_end_tool_call(mocker):
    # Mock triage to route to kb_node
    mocker.patch("ops_pilot.agent.nodes.structured_triage_llm", new=MockTriageLLM())
    from ops_pilot.models.system import System
    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[
            System(
                id="SYS-VPN",
                name="Patliputra VPN",
                status="Operational",
                description="Approved VPN",
            )
        ],
    )
    
    # Mock kb_node LLM to return a tool call
    tool_call = ToolCall(name="search_knowledge_base_tool", args={"title": "VPN"}, id="call_123")
    mocker.patch("ops_pilot.agent.nodes.kb_llm", new=MockKBLLM(tool_call))
    
    from ops_pilot.models.knowledge_base import KnowledgeBase
    # Mock the tool's underlying repo so we don't hit the DB or fail validation
    mocker.patch(
        "ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_keyword",
        return_value=[KnowledgeBase.model_validate({
            "id": "KB-001",
            "title": "VPN Setup",
            "category": "Network",
            "content": "Mocked KB Response",
            "Incident_id": None,
            "tags": [],
        })]
    )
    
    # Re-import create_agent if needed, or just call it since nodes are patched.
    # Wait, graph.py imports triage_node etc. If we patch the module variables in nodes.py, 
    # it affects the functions because the functions read the globals from their module!
    app = create_agent()
    
    # Invoke the graph
    initial_state = AgentState(messages=[HumanMessage(content="How do I connect to VPN?")])
    
    # We can step through or just run it. We will run it completely.
    # The graph will:
    # 1. Start -> triage (routes to kb_node)
    # 2. kb_node -> returns ToolCall -> route_after_agent goes to 'tools'
    # 3. tools -> executes mock tool -> route_after_tools goes back to 'kb_node'
    # 4. kb_node -> we need the mock to return a final answer the second time!
    
    result = app.invoke(
        initial_state,
        config={"configurable": {"thread_id": f"test_1_{uuid.uuid4()}"}},
    )
    
    messages = result.get("messages", [])
    # Check that it reached the final response
    assert messages[-1].content == "Here is how to connect to VPN..."
    assert result["completed_steps"] == [
        "INFRASTRUCTURE_CONTEXT_CHECK",
        "TRIAGE_MANAGER",
        "KNOWLEDGE_BASE_MANAGER",
        "TOOLS",
        "KNOWLEDGE_BASE_MANAGER",
    ]
    assert result["execution_count"] == 5
    
    # Verify the tool call was made (find the message with tool calls)
    tool_calls = [msg for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls]
    assert len(tool_calls) > 0
    assert tool_calls[0].tool_calls[0]["name"] == "search_knowledge_base_tool"


def test_graph_ticket_write_requires_confirmation_before_mutation(mocker):
    from datetime import datetime
    from ops_pilot.models.system import System
    from ops_pilot.models.ticket import Ticket
    from ops_pilot.agent.state import TicketDraft

    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[
            System(
                id="SYS-VPN",
                name="Patliputra VPN",
                status="Operational",
                description="Approved VPN",
            )
        ],
    )
    mocker.patch(
        "ops_pilot.agent.nodes.structured_triage_llm",
        new=MockTriageActionLLM(),
    )
    mocker.patch(
        "ops_pilot.agent.nodes.ticket_write_llm",
        new=MockFinalTicketLLM(),
    )
    mocker.patch(
        "ops_pilot.agent.nodes.ticket_draft_llm",
        new=MockTicketDraftLLM(
            TicketDraft(
                operation="CREATE",
                employee_id="E001",
                title="VPN unavailable",
                description="VPN is unavailable",
                status="Open",
                category="Network",
                ticket_type="INC",
                system_id="SYS-VPN",
            )
        ),
    )
    create_tool = mocker.patch("ops_pilot.agent.nodes.create_ticket_tool")
    create_tool.invoke.return_value = Ticket(
        id="INC-200",
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

    app = create_agent()
    thread_id = f"ticket_confirmation_{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    first = app.invoke(
        AgentState(messages=[HumanMessage(content="Create a ticket because VPN is unavailable")]),
        config=config,
    )

    assert first["awaiting_ticket_confirmation"] is True
    create_tool.invoke.assert_not_called()

    second = app.invoke(
        {"messages": [HumanMessage(content="yes")]},
        config=config,
    )

    create_tool.invoke.assert_called_once()
    assert second["awaiting_ticket_confirmation"] is False
    assert "INC-200" in second["messages"][-1].content


def test_graph_stops_at_out_of_scope_response_before_triage(mocker):
    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[],
    )
    triage = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    app = create_agent()

    result = app.invoke(
        AgentState(messages=[HumanMessage(content="Configure an unsupported satellite service")]),
        config={"configurable": {"thread_id": f"out_of_scope_{uuid.uuid4()}"}},
    )

    assert "supported by Patliputra-Corp" in result["messages"][-1].content
    triage.invoke.assert_not_called()
    assert result["completed_steps"] == [
        "INFRASTRUCTURE_CONTEXT_CHECK",
        "OUT_OF_SCOPE_RESPONSE",
    ]


def test_graph_stops_at_ambiguous_context_response_before_triage(mocker):
    from ops_pilot.models.system import System

    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[
            System(id="SYS-A", name="Acme Internet", status="Online"),
            System(id="SYS-B", name="Bharat Internet", status="Online"),
        ],
    )
    triage = mocker.patch("ops_pilot.agent.nodes.structured_triage_llm")
    app = create_agent()

    result = app.invoke(
        AgentState(messages=[HumanMessage(content="internet reimbursement")]),
        config={"configurable": {"thread_id": f"ambiguous_{uuid.uuid4()}"}},
    )

    assert "Acme Internet (SYS-A)" in result["messages"][-1].content
    assert "Bharat Internet (SYS-B)" in result["messages"][-1].content
    triage.invoke.assert_not_called()


def test_checkpointed_conversation_does_not_exhaust_step_budget(mocker):
    mocker.patch(
        "ops_pilot.agent.nodes.system_repository.search_supported_systems_from_request",
        return_value=[],
    )
    app = create_agent()
    thread_id = f"many_turns_{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    for turn in range(13):
        result = app.invoke(
            {"messages": [HumanMessage(content=f"Unsupported request turn {turn}")]},
            config=config,
        )

    assert result["execution_count"] == 2
    assert result["completed_steps"] == [
        "INFRASTRUCTURE_CONTEXT_CHECK",
        "OUT_OF_SCOPE_RESPONSE",
    ]


class MockTriageActionLLM:
    def invoke(self, *args, **kwargs):
        return TriageDecision(
            next_node="TICKET_ACTION_REQUEST",
            routing_reason="The user explicitly requested a ticket.",
        )


class MockFinalTicketLLM:
    def invoke(self, *args, **kwargs):
        return AIMessage(content="Ticket details prepared.")


class MockTicketDraftLLM:
    def __init__(self, draft):
        self.draft = draft

    def invoke(self, *args, **kwargs):
        return self.draft
