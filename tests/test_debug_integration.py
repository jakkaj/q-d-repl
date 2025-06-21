"""
Test file for debugging the smart debugger with integration pipeline tests.
"""

import networkx as nx


def create_simple_graph():
    """Create a simple graph for testing."""
    graph = nx.DiGraph()
    graph.add_node("node1", type="function", name="test_func")
    graph.add_node("node2", type="class", name="TestClass")
    graph.add_edge("node1", "node2", relationship="calls")
    return graph


def test_simple_graph_debug():
    """Simple test to debug graph inspection."""
    # Create a graph
    graph = create_simple_graph()

    # Line 20 - Good breakpoint location
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1

    # Get graph info
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    # Line 28 - Another good breakpoint
    print(f"Graph has {node_count} nodes and {edge_count} edges")

    # No return in pytest tests


def test_graph_with_data():
    """Test with more complex graph data."""
    graph = nx.DiGraph()

    # Add some nodes with data
    for i in range(5):
        graph.add_node(f"node_{i}", type="function", name=f"func_{i}", line_no=i * 10)

    # Add edges
    for i in range(4):
        graph.add_edge(f"node_{i}", f"node_{i+1}")

    # Line 49 - Breakpoint for complex graph
    nodes = list(graph.nodes())
    edges = list(graph.edges())

    print(f"Nodes: {nodes}")
    print(f"Edges: {edges}")

    # Verify the graph
    assert len(nodes) == 5
    assert len(edges) == 4


if __name__ == "__main__":
    # Simple test runner
    print("Running test_simple_graph_debug...")
    graph1 = test_simple_graph_debug()
    print(f"Graph 1 complete: {graph1}")

    print("\nRunning test_graph_with_data...")
    graph2 = test_graph_with_data()
    print(f"Graph 2 complete: {graph2}")
