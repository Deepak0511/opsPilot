import pytest
from ops_pilot.agent.graph import create_agent

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
        assert len(mermaid) > 0
    except Exception as e:
        pytest.fail(f"Could not draw mermaid graph: {e}")
