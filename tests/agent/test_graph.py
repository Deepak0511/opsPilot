import pytest
from ops_pilot.agent.graph import create_agent
from ops_pilot.agent.state import TriageDecision
from langchain_core.messages import HumanMessage, AIMessage, ToolCall

def test_create_agent():
    # Calling create_agent compiles the graph.
    # We just want to ensure it compiles without errors
    # and has the expected nodes and edges.
    app = create_agent()
    
    assert app is not None
    
    # Check if expected nodes exist in the compiled graph's nodes mapping
    nodes = app.nodes.keys()
    expected_nodes = [
        "triage", 
        "kb_node", 
        "infra_node", 
        "ticket_read_node", 
        "ticket_logger_node", 
        "tools"
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
        return TriageDecision(next_node="kb_node")

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
    
    # Mock kb_node LLM to return a tool call
    tool_call = ToolCall(name="search_knowledge_base_tool", args={"title": "VPN"}, id="call_123")
    mocker.patch("ops_pilot.agent.nodes.kb_llm", new=MockKBLLM(tool_call))
    
    from ops_pilot.models.knowledge_base import KnowledgeBase
    # Mock the tool's underlying repo so we don't hit the DB or fail validation
    mocker.patch(
        "ops_pilot.tools.kb_toolchain.kb_repository.search_knowledge_base_by_title", 
        return_value=[KnowledgeBase(id="KB-001", title="VPN Setup", category="Network", content="Mocked KB Response", tags=[])]
    )
    
    # Re-import create_agent if needed, or just call it since nodes are patched.
    # Wait, graph.py imports triage_node etc. If we patch the module variables in nodes.py, 
    # it affects the functions because the functions read the globals from their module!
    app = create_agent()
    
    # Invoke the graph
    initial_state = {"messages": [HumanMessage(content="How do I connect to VPN?")]}
    
    # We can step through or just run it. We will run it completely.
    # The graph will:
    # 1. Start -> triage (routes to kb_node)
    # 2. kb_node -> returns ToolCall -> route_after_agent goes to 'tools'
    # 3. tools -> executes mock tool -> route_after_tools goes back to 'kb_node'
    # 4. kb_node -> we need the mock to return a final answer the second time!
    
    result = app.invoke(initial_state, config={"configurable": {"thread_id": "test_1"}})
    
    messages = result.get("messages", [])
    # Check that it reached the final response
    assert messages[-1].content == "Here is how to connect to VPN..."
    
    # Verify the tool call was made (find the message with tool calls)
    tool_calls = [msg for msg in messages if hasattr(msg, "tool_calls") and msg.tool_calls]
    assert len(tool_calls) > 0
    assert tool_calls[0].tool_calls[0]["name"] == "search_knowledge_base_tool"
