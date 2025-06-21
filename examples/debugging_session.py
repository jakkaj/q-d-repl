"""
Example: Using the Smart Debugger

This example shows how to use the smart debugger to debug pytest tests
without modifying source code.
"""

# Example 1: Basic breakpoint with inspection
print("Example 1: Set breakpoint and inspect variable")
print("Run this command:")
print('python3 -m smart_debugger.pytest_breakrepl tests/sample_projects/simple_project/test_example.py 9 "print(\'total:\', total, \'num:\', num)" -- -v -s')
print()

# Example 2: Breakpoint without initial command (interactive only)  
print("Example 2: Interactive debugging session")
print("Run this command:")
print('python3 -m smart_debugger.pytest_breakrepl tests/sample_projects/simple_project/test_example.py 9 "" -- -v -s')
print("Then use these commands in the debugger:")
print("  l          # List source code")
print("  p total    # Print value of total")
print("  pp locals()  # Pretty-print all local variables")
print("  c          # Continue execution")
print()

# Example 3: Complex inspection
print("Example 3: Load helper functions for analysis")
print("Run this command:")
print('python3 -m smart_debugger.pytest_breakrepl tests/sample_projects/simple_project/test_example.py 28 "print(\'User data:\', user_data)" -- -v -s')
print()

# Example 4: Multiple iterations
print("Example 4: See each iteration of a loop")
print("The breakpoint at line 9 will be hit for each number in the list.")
print("You can inspect how 'total' changes with each iteration.")
print()

print("Tips:")
print("- Use -s flag with pytest to see output and allow interaction")
print("- Press 'c' in the debugger to continue execution")
print("- Press 'q' to quit the debugger")
print("- Use 'help' to see all available commands")