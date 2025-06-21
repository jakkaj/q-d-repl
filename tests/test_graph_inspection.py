"""
Test to inspect graph structures similar to integration pipeline.
"""
import sys
import os
sys.path.insert(0, '/workspaces/substrate')

import networkx as nx
from pathlib import Path

def test_mock_integration_graph():
    """Create a mock graph similar to what integration pipeline would have."""
    # Create a graph similar to what the pipeline would generate
    graph = nx.DiGraph()
    
    # Add some mock nodes like the real pipeline would
    graph.add_node("file:src/main.py", type="file", path="src/main.py")
    graph.add_node("class:MainClass", type="class", name="MainClass", file="src/main.py")
    graph.add_node("function:main", type="function", name="main", file="src/main.py")
    graph.add_node("function:helper", type="function", name="helper", file="src/main.py")
    
    # Add relationships
    graph.add_edge("file:src/main.py", "class:MainClass", relationship="contains")
    graph.add_edge("file:src/main.py", "function:main", relationship="contains")
    graph.add_edge("class:MainClass", "function:helper", relationship="contains")
    graph.add_edge("function:main", "function:helper", relationship="calls")
    
    # Line 27 - Good breakpoint to inspect the graph
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    # Print first few nodes and edges
    print("\nFirst 3 nodes:")
    for node, data in nodes[:3]:
        print(f"  {node}: {data}")
    
    print("\nFirst 3 edges:")  
    for source, target, data in edges[:3]:
        print(f"  {source} -> {target}: {data}")
    
    # Assert some basic properties
    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 4