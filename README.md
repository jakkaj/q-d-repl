# Smart Debugger

A non-interactive debugging tool for Python that enables developers and automated systems to inspect running code without modifying source files.

## Overview

Smart Debugger allows you to set breakpoints in Python code and execute arbitrary commands at those breakpoints, all without requiring interactive sessions or polluting your codebase with debug prints. It supports both pytest tests and standalone Python scripts, making it a versatile tool for automated debugging, code analysis, and LLM-assisted development.

## Key Features

- **Non-Interactive**: Set breakpoint, execute command, get output, exit cleanly
- **No Code Modification**: Inspect variables without adding print statements
- **Dual Mode Support**: Debug both pytest tests and standalone Python scripts
- **Module Execution**: Support for `python -m` style module debugging
- **Complex Expressions**: Support for multiline commands and JSON formatting
- **Clean Output**: Optional quiet mode for minimal, parseable output
- **Global Access**: Available system-wide via `pydebug` and `pydebug-stdin` commands

## Standalone Python Debugging

Smart Debugger now supports debugging ANY Python file, not just pytest tests. Use the `--mode` flag to switch between pytest (default) and standalone modes.

### Basic Script Debugging
```bash
# Debug a regular Python script
pydebug --mode standalone script.py 25 "print(variable_name)"

# With stdin for complex expressions
echo "print(f'Value: {x}, Type: {type(x).__name__}')" | \
  pydebug-stdin --mode standalone script.py 25
```

### Module Debugging
```bash
# Debug a Python module (like python -m module.name)
pydebug --mode standalone -m my.module 30 "print(config)"

# With stdin
echo "import json; print(json.dumps(data, indent=2))" | \
  pydebug-stdin --mode standalone -m my.module 30
```

### Passing Script Arguments
```bash
# Pass arguments to your script after --
pydebug --mode standalone script.py 15 "print(sys.argv)" -- arg1 arg2 --option=value

# With module and arguments
pydebug --mode standalone -m my.app 20 "print(args)" -- --config=prod --verbose
```

### Quiet Mode with Standalone
```bash
# Clean output for automation
echo "print(result)" | pydebug-stdin --quiet --mode standalone app.py 42

# Module with quiet mode
echo "print(state)" | pydebug-stdin -q --mode standalone -m server.main 100
```

### Real-World Examples

**Debug a Flask Application**
```bash
# Inspect request handling
echo 'print(f"Request: {request.method} {request.path}")
print(f"Headers: {dict(request.headers)}")' | \
  pydebug-stdin --quiet --mode standalone -m flask run 150
```

**Debug a CLI Tool**
```bash
# Check argument parsing
pydebug --mode standalone cli_tool.py 45 "print(parsed_args)" -- --help
```

**Debug a Data Processing Script**
```bash
# Inspect data transformations
echo 'print(f"Input shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head())' | \
  pydebug-stdin --quiet --mode standalone process_data.py 80 -- input.csv output.csv
```

## Quick Start

### Installation

```bash
# Add to your PATH (or use absolute paths)
export PATH="/workspaces/q-d-repl:$PATH"
```

### Basic Usage

```bash
# Debug pytest tests (default mode)
pydebug test_file.py 42 "print(variable_name)"

# Debug standalone Python scripts
pydebug --mode standalone script.py 42 "print(variable_name)"

# Complex debugging with file parameter (recommended for complex debugging)
echo 'print(f"Value: {x}, Type: {type(x).__name__}")' > debug.py
pydebug-stdin -f debug.py --quiet test_file.py 42

# Production debugging pattern - debug source code by running tests
pydebug-stdin --quiet -f scratch/debug.py src/modules/condense.py 150 -- tests/test_integration.py::TestClass::test_method -v

# Inline debugging with stdin
echo "print(f'Value: {x}, Type: {type(x).__name__}')" | pydebug-stdin test_file.py 42

# Quiet mode for clean output (recommended for automation)
echo "print(result)" | pydebug-stdin --quiet test_file.py 42
```

## Core Concepts

### How It Works

```mermaid
graph TD
    A[Developer/Script] -->|"pydebug file.py 42 'print(x)'"| B[Smart Debugger]
    A -->|"echo 'print(x)' | pydebug-stdin file.py 42"| B
    
    B --> C{Mode?}
    C -->|pytest<br/>(default)| D[Launch pytest]
    C -->|standalone| E[Launch Python directly]
    
    D --> F[Set sys.settrace]
    E --> F
    F --> G[Execute Python Code]
    
    G --> H{Line 42 Hit?}
    H -->|No| G
    H -->|Yes| I[Execute Debug Command]
    
    I --> J[Capture Output]
    J --> K[Stop Tracing]
    K --> L[Clean Exit]
    
    L --> M[Output Results]
    M -->|Normal Mode| N[Full output<br/>+ Debug output]
    M -->|Quiet Mode| O[Debug output only<br/>Version banner on stderr]
```

**Process Overview:**

1. **Set Breakpoint**: Specify file and line number where you want to inspect code
2. **Execute Command**: Provide a Python expression or statement to execute
3. **Get Results**: The debugger runs your code, hits the breakpoint, executes your command, and exits
4. **Clean Exit**: No interaction required, perfect for automation

### Three Usage Methods

**Method 1: File Parameter (Recommended for Complex Debugging)**
```bash
# Write debug script
echo 'print(variable)' > debug.py
# Run with file parameter
pydebug-stdin -f debug.py --quiet test.py 42 -- -v
```

**Method 2: Stdin (Good for Inline Commands)**
```bash
echo "print(variable)" | pydebug-stdin file.py 42
```

**Method 3: Direct Command (Simple Cases Only)**
```bash
pydebug file.py 42 "print(variable)"
```

The file parameter method is recommended for:
- Complex debugging sessions with multiple statements
- Reusable debug scripts
- Production debugging patterns
- Avoiding shell escaping issues

The stdin method is preferred for:
- Quick one-line debugging
- Multiline commands without saving to file
- Automated scripts with dynamic commands

Direct command is only for:
- Very simple, single-line expressions
- Quick interactive debugging

### File Parameter Method in Detail

The file parameter method (`-f` or `--file`) is the most powerful way to use Smart Debugger:

```bash
# Basic file parameter usage
echo 'print(variable)' > debug.py
pydebug-stdin -f debug.py --quiet test.py 42

# Multiline debug script
cat > debug_script.py << 'EOF'
# Comprehensive debugging
import json
import pprint

print("=== Debug Session ===")
print(f"Available variables: {list(locals().keys())}")

# Pretty print complex objects
if 'data' in locals():
    pprint.pprint(data)
    
# JSON output for structured data
if 'config' in locals():
    print(json.dumps(config, indent=2))
EOF

pydebug-stdin -f debug_script.py --quiet src/module.py 100
```

**Production Debugging Pattern:**
```bash
# Debug production code by running specific tests
# This lets you set breakpoints in source code and run tests to hit them
pydebug-stdin --quiet -f scratch/debug.py src/modules/condense.py 150 -- tests/test_integration.py::TestClass::test_method -v

# Debug with multiple test scenarios
pydebug-stdin --quiet -f debug_analysis.py src/api/handler.py 200 -- tests/test_api.py -k "error_handling or edge_case" -v
```

**Advantages of File Parameter:**
- No shell escaping issues with quotes or special characters
- Reusable debug scripts for common debugging patterns
- Easy to version control debug scripts
- Can include complex logic, imports, and multiline code
- Perfect for production debugging scenarios

## Real-World Examples

### Test Debugging (Pytest Mode - Default)
```bash
# Test fails - inspect the actual vs expected values
echo 'print(f"Expected: {expected}")
print(f"Actual: {actual}")
print(f"Difference: {set(expected) - set(actual)}")' | \
  pydebug-stdin tests/test_example.py 85 --quiet
```

### Production Debugging with File Parameter
```bash
# Create a reusable debug script
cat > debug_production.py << 'EOF'
import json
import sys

# Inspect the current state
print("=== Debug Information ===")
print(f"Python version: {sys.version}")
print(f"Local variables: {list(locals().keys())}")

# Check specific variables if they exist
if 'request' in locals():
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"Headers: {dict(request.headers)}")

if 'response' in locals():
    print(f"Response status: {response.status_code}")
    print(f"Response data: {json.dumps(response.json(), indent=2)}")

if 'error' in locals():
    print(f"Error type: {type(error).__name__}")
    print(f"Error message: {str(error)}")
EOF

# Debug production code by running specific test
pydebug-stdin --quiet -f debug_production.py src/api/handlers.py 245 -- tests/test_api.py::TestAPIHandler::test_error_handling -v
```

### Data Structure Analysis (Standalone Mode)
```bash
# Pretty-print complex data structures in a regular Python script
echo 'import json; print(json.dumps(result_data, indent=2, default=str))' | \
  pydebug-stdin --mode standalone src/processor.py 150 --quiet
```

### Performance Investigation (Standalone Mode)
```bash
# Check object sizes and types in a Python script
echo 'import sys
print(f"Object type: {type(data_structure)}")
print(f"Size: {sys.getsizeof(data_structure)} bytes")
print(f"Length: {len(data_structure)}")' | \
  pydebug-stdin --mode standalone src/analyzer.py 200 --quiet
```

## Command Line Options

### Basic Syntax
```bash
pydebug [--quiet] [--mode MODE] [-m MODULE | FILE] <line> "<command>" [-- args]
echo "<command>" | pydebug-stdin [--quiet] [--mode MODE] [-m MODULE | FILE] <line> [-- args]
pydebug-stdin -f <debug_script> [--quiet] [--mode MODE] [-m MODULE | FILE] <line> [-- args]
```

### Options
- `--file` or `-f`: Read debug commands from a file (recommended for complex debugging)
- `--quiet` or `-q`: Show only command output (recommended for automation)
- `--mode`: Execution mode: `pytest` (default) or `standalone`
- `-m MODULE`: Run as module (like `python -m MODULE`) - only in standalone mode
- `-- args`: Pass additional arguments to pytest or the script/module

### Examples with Options
```bash
# Run pytest with verbose mode (default mode)
pydebug test.py 42 "print(x)" -- -v

# Debug standalone script with arguments
pydebug --mode standalone script.py 30 "print(args)" -- --input=data.csv

# Debug with file parameter for complex analysis
cat > debug_analysis.py << 'EOF'
import json
print("Local variables:", {k: type(v).__name__ for k, v in locals().items()})
if 'data' in locals():
    print(f"Data type: {type(data)}")
    print(f"Data sample: {json.dumps(data[:5], indent=2)}")
EOF
pydebug-stdin -f debug_analysis.py --quiet src/processor.py 75

# Production debugging - debug source by running specific test
pydebug-stdin --quiet -f scratch/inspect_state.py src/core/engine.py 200 -- tests/test_engine.py::test_state_handling -xvs

# Debug module with quiet mode
echo "print(config)" | pydebug-stdin -q --mode standalone -m my.app 50

# Quiet mode with specific pytest test selection
echo "print(result)" | pydebug-stdin --quiet test.py 42 -- -k "test_specific"
```

## Output Modes

### Normal Mode
Shows full output from the execution:
- **Pytest mode**: Full pytest output including test collection, execution details, and your debug output
- **Standalone mode**: Full Python execution output and your debug output

### Quiet Mode (Recommended)
Shows only:
- Your debug command output (stdout)
- Version banner and breakpoint location (stderr)
- Warnings if no output captured (stderr)

Quiet mode reduces output by 90%+ making it ideal for automation and scripting.

## Integration Examples

### CI/CD Debugging
```bash
# Debug failing tests in CI without modifying code
echo 'print("Debug info:", locals().keys())' | \
  pydebug-stdin --quiet tests/test_integration.py 100

# Use file parameter for complex CI debugging
cat > ci_debug.py << 'EOF'
import os
import json

print(f"CI Environment: {os.environ.get('CI', 'Not in CI')}")
print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Current directory: {os.getcwd()}")
print(f"Local variables: {list(locals().keys())}")

# Check test-specific variables
if 'pytest_config' in locals():
    print(f"Pytest config: {pytest_config}")
EOF

pydebug-stdin -f ci_debug.py --quiet tests/test_integration.py 100
```

### Code Analysis Scripts
```bash
#!/bin/bash
# Extract runtime type information
for line in 50 75 100; do
  echo "print(f'Line $line: {type(result).__name__}')" | \
    pydebug-stdin --quiet src/analyzer.py $line
done

# Or use a file for more complex analysis
cat > analyze_types.py << 'EOF'
import inspect

def analyze_object(obj, name):
    print(f"\n{name} Analysis:")
    print(f"  Type: {type(obj).__name__}")
    print(f"  Module: {inspect.getmodule(obj)}")
    if hasattr(obj, '__dict__'):
        print(f"  Attributes: {list(obj.__dict__.keys())[:5]}")

# Analyze all objects in scope
for var_name, var_value in locals().items():
    if not var_name.startswith('_'):
        analyze_object(var_value, var_name)
EOF

for line in 50 75 100; do
  pydebug-stdin -f analyze_types.py --quiet src/analyzer.py $line
done
```

### Development Workflow
```bash
# Quick variable inspection during development
alias debug-here='echo "print(locals())" | pydebug-stdin --quiet'
debug-here myfile.py 42

# Create a debug alias with file parameter for complex debugging
alias debug-prod='pydebug-stdin --quiet -f ~/.debug_scripts/prod_debug.py'
# Usage: debug-prod src/module.py 150 -- tests/test_module.py::specific_test -v
```

## Best Practices

### For Automation
- Always use `--quiet` mode for scripts and automated systems
- Use file parameter (`-f`) for reusable debug scripts
- Prefer `pydebug-stdin` for complex expressions
- Use JSON formatting for structured data output
- Capture stderr for breakpoint confirmation

### For Development
- Create debug script files in a `scratch/` directory for complex debugging
- Use the production debugging pattern: debug source code by running specific tests
- Use descriptive commands that explain what you're inspecting
- Leverage Python's introspection capabilities (`type()`, `dir()`, `vars()`)
- Combine with version control to track debugging sessions

### For Testing
- Debug test failures without modifying test files
- Use to inspect test data and fixtures
- Combine with pytest markers and filters
- Debug production code issues by setting breakpoints in source while running tests

## Troubleshooting

### Common Issues

**Breakpoint Not Hit**
- Verify the line number contains executable code
- Check that the line is actually reached during execution
- For pytest mode: Use `-v` flag to see test execution flow
- For standalone mode: Add print statements before the target line to verify execution path

**Command Errors**
- Ensure variables exist at the breakpoint location
- Use `locals()` to see available variables
- Check Python syntax in your debug command

**Output Issues**
- Use `--quiet` for clean output
- Check stderr for error messages and warnings
- Ensure proper quoting in complex expressions

### Tips
- Start with simple commands like `print(locals())` to see available variables
- Use `type()` and `dir()` to understand object structure
- Leverage `json.dumps()` for complex data visualization

## Global Installation

To make the debugger available system-wide:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export PATH="/workspaces/q-d-repl:$PATH"

# Or create symbolic links
ln -s /workspaces/q-d-repl/pydebug /usr/local/bin/pydebug
ln -s /workspaces/q-d-repl/pydebug-stdin /usr/local/bin/pydebug-stdin
```

## Advanced Usage

### Custom Pytest Arguments (Pytest Mode)
```bash
# Run with coverage and verbose output
echo "print(coverage_data)" | \
  pydebug-stdin test.py 42 -- --cov=src --cov-report=term -v
```

### Complex Debugging Sessions with File Parameter
```bash
# Create a comprehensive debug script for analyzing a complex system
cat > debug_comprehensive.py << 'EOF'
import json
import inspect
import gc
import sys

print("=== System State Analysis ===")

# Memory usage
print(f"\nMemory objects by type:")
type_counts = {}
for obj in gc.get_objects():
    type_name = type(obj).__name__
    type_counts[type_name] = type_counts.get(type_name, 0) + 1

top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
for type_name, count in top_types:
    print(f"  {type_name}: {count}")

# Local state analysis
print(f"\nLocal variables ({len(locals())} total):")
for name, value in sorted(locals().items()):
    if not name.startswith('_'):
        print(f"  {name}: {type(value).__name__}")
        if hasattr(value, '__len__'):
            try:
                print(f"    Length: {len(value)}")
            except:
                pass

# Stack trace
print(f"\nCall stack depth: {len(inspect.stack())}")
for i, frame_info in enumerate(inspect.stack()[:5]):
    print(f"  {i}: {frame_info.filename}:{frame_info.lineno} in {frame_info.function}")

# Specific object analysis
if 'target_object' in locals():
    obj = locals()['target_object']
    print(f"\nTarget object analysis:")
    print(f"  Type: {type(obj)}")
    print(f"  ID: {id(obj)}")
    print(f"  Size: {sys.getsizeof(obj)} bytes")
    print(f"  Attributes: {[a for a in dir(obj) if not a.startswith('_')][:10]}")
EOF

# Run comprehensive debugging on production code
pydebug-stdin --quiet -f debug_comprehensive.py src/core/processor.py 350 -- tests/test_processor.py::test_memory_usage -v
```

### Complex Data Analysis (Standalone Mode)
```bash
# Analyze object relationships in a Python script
echo 'import inspect
print("Methods:", [m for m in dir(obj) if callable(getattr(obj, m))])
print("Properties:", [p for p in dir(obj) if not callable(getattr(obj, p))])
print("MRO:", [cls.__name__ for cls in type(obj).__mro__])' | \
  pydebug-stdin --quiet --mode standalone src/complex_object.py 75
```

### Batch Debugging (Works with Both Modes)
```bash
# Debug multiple points in sequence (pytest mode - default)
for line in 10 20 30 40; do
  echo "print(f'Line {$line}: {locals()}')" | \
    pydebug-stdin --quiet test_myfile.py $line
done

# Debug multiple points in a standalone script
for line in 10 20 30 40; do
  echo "print(f'Line {$line}: {locals()}')" | \
    pydebug-stdin --quiet --mode standalone script.py $line
done
```

## Contributing

When contributing to this project:
- Follow the established code patterns
- Add tests for new functionality
- Update documentation for new features
- Ensure backward compatibility

## License

[License information here]

---

*Smart Debugger: Clean, non-interactive debugging for modern development workflows.*