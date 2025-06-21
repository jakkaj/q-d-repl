#!/usr/bin/env python3
"""
Helper script to execute multiline debug commands.
Usage:
1. Save your multiline command to a file (e.g., debug_cmd.py)
2. Run: pydebug <file> <line> "exec(open('/path/to/debug_cmd.py').read())" -- [pytest args]
"""

# Example multiline debug command that can be saved to a file:
print(
    """
THE GRAPH HAS:
- Nodes: {graph.number_of_nodes()}
- Edges: {graph.number_of_edges()}
""".format(
        graph=graph
    )
)

# You can also inspect variables:
print(f"Graph type: {type(graph)}")
print(f"Graph nodes sample: {list(graph.nodes())[:5]}")
