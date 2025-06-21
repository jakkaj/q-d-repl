# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL: Debugging Requirements

**NEVER insert debug outputs directly into code!** Always use the Smart Debugger for debugging ANY Python code:
- ❌ **DO NOT** add `print()` statements to source files for debugging
- ❌ **DO NOT** insert `import pdb; pdb.set_trace()` or similar debugger calls
- ❌ **DO NOT** modify test files with debug output
- ❌ **DO NOT** run debug commands from terminal like `python3 -m pdb`
- ✅ **ALWAYS** use `pydebug-stdin` with the `-f` file parameter for reliable debugging
- ✅ **ALWAYS** use the `--quiet` flag to minimize output for LLM agents
- ✅ **SUPPORTS** both pytest tests and standalone Python scripts/modules

### How to Debug Tests and Code

**MOST PREFERRED METHOD**: Use `pydebug-stdin` with the `-f` file parameter for maximum reliability and flexibility. Debug production code by running tests that exercise it.

**Basic Pattern:**
```bash
# MOST PREFERRED: Use the debug script file parameter
# First write the file then run. You place breakpoint in the file you want, then you run the test that calls that file.
# It's best to run from tests so you isolate the code.
pydebug-stdin --quiet -f scratch/debug.py src/modules/condense.py 150 -- tests/test_smart_content/test_integration_pipeline.py::TestSmartContentIntegrationPipeline::test_complete_pipeline_with_real_llm -v

# Step-by-step:
# 1. Write debug commands to a file
echo "print(variable_name)" > scratch/debug.py

# 2. Use the debug script file with test-driven approach
pydebug-stdin -f scratch/debug.py [--mode MODE] --quiet file.py line_number -- test_file.py::test_name -v
```

**Alternative Method (stdin piping for quick checks):**
```bash
echo "command" | pydebug-stdin [--mode MODE] --quiet file.py line_number
```

**Debugging Tests (default mode):**
```bash
# MOST PREFERRED: Test-driven debugging with file parameter
# Step 1: Create debug script
cat > scratch/debug_data.py << 'EOF'
import json
print("=== Debug Output ===")
print(f'Type: {type(data)}, Length: {len(data) if hasattr(data, "__len__") else "N/A"}')
print(f'Value: {data}')
if hasattr(data, '__dict__'):
    print("Object attributes:")
    print(json.dumps(vars(data), indent=2))
EOF

# Step 2: Debug production code by running test that exercises it
pydebug-stdin -f scratch/debug_data.py --quiet src/data_processor.py 60 -- tests/test_data_processor.py::test_process_data -v

# Alternative: Quick inspection with stdin piping
echo "print(variable_name)" | pydebug-stdin --quiet /path/to/test_file.py 42
```

**Debugging Standalone Python Scripts:**
```bash
# MOST PREFERRED: Debug production code through tests
# Step 1: Create comprehensive debug script
cat > scratch/debug_module.py << 'EOF'
import json
import sys
print("=== Module Debug Info ===")
print(f"Python path: {sys.path[0]}")
print(f"Arguments: {sys.argv}")
if 'config' in locals():
    print(f"Config loaded: {json.dumps(config, indent=2)}")
print(f"Local variables: {list(locals().keys())}")
EOF

# Step 2: Debug by running test that exercises the module
pydebug-stdin --quiet -f scratch/debug_module.py src/modules/condense.py 150 -- tests/test_smart_content/test_integration_pipeline.py::TestSmartContentIntegrationPipeline::test_complete_pipeline_with_real_llm -v

# Alternative: Direct standalone debugging (when test approach not applicable)
echo "print(config)" | pydebug-stdin --mode standalone --quiet /path/to/script.py 42
```

**Why file parameter (-f) is MOST preferred:**
- **Test-driven debugging**: Debug production code safely by running tests that exercise it
- **Isolation**: Tests provide controlled environment for debugging
- **Complex debugging**: Write sophisticated multiline debug scripts
- **Reusability**: Save debug scripts in `scratch/` for repeated use
- **No shell escaping**: Avoid quote and escape character issues
- **Version control**: Track and share debug approaches
- **Production safety**: Never debug production directly, always through tests

**When to use stdin method:**
- Quick one-line variable checks
- Simple print statements
- When piping from other commands
- Exploratory debugging

The `pydebug-stdin` tool will:
- Set breakpoints automatically at the specified line
- Execute your piped commands at the breakpoint
- Return clean output with `--quiet` mode
- Exit cleanly without requiring interaction
- Support both pytest test debugging and standalone Python debugging

#### File Parameter with Quiet Mode (Most Preferred for LLM Agents)

**IMPORTANT**: LLM agents should ALWAYS use `pydebug-stdin -f scratch/debug.py --quiet` with test-driven debugging by default. This ensures reliable command execution and production code safety.

**Basic file parameter pattern with quiet mode:**
```bash
# Step 1: Write debug command to scratch directory
echo "print(variable_name)" > scratch/debug.py

# Step 2: Debug production code through test execution
pydebug-stdin -f scratch/debug.py --quiet src/module.py line_number -- tests/test_module.py::test_case -v
```

**Advanced file parameter examples:**
```bash
# MOST PREFERRED: Comprehensive debug script for production code
cat > scratch/debug_analysis.py << 'EOF'
import json
import traceback

print("=== Debug Analysis ===")
print(f"Call stack:")
for line in traceback.format_stack()[-3:-1]:
    print(line.strip())

# Analyze the data structure
if 'data' in locals():
    print(f"\nData type: {type(data).__name__}")
    print(f"Data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
    print("\nData contents:")
    try:
        print(json.dumps(data, indent=2, default=str))
    except:
        print(repr(data)[:500])
EOF

# Debug production code through test
pydebug-stdin -f scratch/debug_analysis.py --quiet src/processor.py 42 -- tests/test_processor.py::test_data_processing -v
```

#### Alternative: Stdin Method with Quiet Mode (For Quick Checks)

**When to use stdin instead of file parameter:**
- Quick one-line debugging commands
- Piping output from other tools
- Dynamic command generation in scripts

**Stdin examples:**
```bash
# Multiple statements (semicolon-separated)
echo "import json; print(json.dumps(data, indent=2))" | pydebug-stdin --quiet tests/test_example.py 42

# Complex expressions with f-strings
echo "print(f'Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges')" | pydebug-stdin --quiet tests/test_graph.py 75

# Local variable inspection
echo "print({k: type(v).__name__ for k, v in locals().items() if not k.startswith('_')})" | pydebug-stdin --quiet src/module.py 60
```

**Quiet mode output example:**
```bash
$ echo "print({'key': 'value'})" | pydebug-stdin --quiet tests/test_example.py 42
{'key': 'value'}
Smart Debugger v1.2.0 - Non-interactive debugging for LLM agents
Breakpoint hit: /path/to/tests/test_example.py:42
```

**When no output is captured:**
```bash
$ echo "pass" | pydebug-stdin --quiet tests/test_example.py 42
Smart Debugger v1.2.0 - Non-interactive debugging for LLM agents
Breakpoint hit: /path/to/tests/test_example.py:42
Warning: No output captured from REPL command
```

**Advantages of stdin method:**
- **Multiline commands**: Handle complex expressions without shell escaping
- **No line wrapping**: Avoid terminal width limitations
- **JSON formatting**: Perfect for structured data output
- **Robust parsing**: No issues with quotes, spaces, or special characters
- **LLM-friendly**: Predictable input/output patterns

**When to use normal mode (without --quiet):**
- Only when you need to see full pytest collection output
- When debugging test discovery issues
- When you need to see the complete test execution flow

For 99% of debugging tasks, `pydebug-stdin -f scratch/debug.py --quiet` with test-driven debugging provides the most reliable and safe approach while conserving valuable token space.

## Project Overview

Smart Debugger is a non-interactive Python debugging tool that enables developers and automated systems to inspect running code without modifying source files. It supports both pytest tests AND standalone Python scripts, making it a versatile tool for automated debugging, code analysis, and LLM-assisted development.

## Key Features

- **Non-Interactive**: Set breakpoint, execute command, get output, exit cleanly
- **No Code Modification**: Inspect variables without adding print statements
- **Dual Mode Support**: Debug both pytest tests and standalone Python scripts
- **Module Execution**: Support for `python -m` style module debugging
- **Complex Expressions**: Support for multiline commands and JSON formatting
- **Clean Output**: Optional quiet mode for minimal, parseable output
- **Global Access**: Available system-wide via `pydebug` and `pydebug-stdin` commands

## Development Commands

### Essential Commands
```bash
# Run all tests
just test

# Run unit tests only
just test-unit

# Run integration tests
just test-integration

# Format and fix code automatically 
just fix

# Run all quality checks (lint, format check, type check)
just quality

# Type checking and linting
just lint

# Install in development mode
just dev-install

# Clean up generated files
just clean
```

### Debugging Commands (Using Smart Debugger)
```bash
# Debug any test file at specific line
just debug-test <file> <line> "<command>"

# Example debugging session
just debug-example

# Debug loop iteration
just debug-loop

# Direct usage for custom debugging
# MOST PREFERRED: File parameter with test-driven approach
echo "print(variable)" > scratch/debug.py
pydebug-stdin --quiet -f scratch/debug.py src/module.py 42 -- tests/test_module.py::test_case -v

# Alternative: Stdin for quick checks
echo "print(variable)" | pydebug-stdin --quiet tests/test_file.py 42 -- -v
```

## File Structure

### Core Components
- `smart_debugger/` - Main debugger package
  - `__main__.py` - CLI entry point
  - `non_interactive.py` - Core debugging logic
  - `standalone.py` - Standalone Python script support
- `pydebug` - Global command wrapper
- `pydebug-stdin` - Command wrapper supporting both file parameter and stdin
- `tests/` - Test suite with sample projects
- `examples/` - Usage examples and patterns

### Test Organization
- `tests/sample_projects/` - Example projects for testing
- `tests/test_*.py` - Unit and integration tests
- Comprehensive test coverage for both pytest and standalone modes

## Development Patterns

### Using the Smart Debugger for Development

**CRITICAL**: Always use the Smart Debugger instead of modifying code:

```bash
# ❌ WRONG - Never do this:
# Adding print statements to debug
def my_function():
    result = calculate_something()
    print(f"DEBUG: result={result}")  # DON'T DO THIS
    return result

# ✅ CORRECT - Use pydebug-stdin with file parameter and test-driven debugging:
# Step 1: Write debug script
echo "print(f'result={result}')" > scratch/debug_result.py
# Step 2: Debug by running test that exercises this code
pydebug-stdin --quiet -f scratch/debug_result.py src/my_module.py 45 -- tests/test_my_module.py::test_calculate -v
```

#### Common Debugging Scenarios

**Test Debugging (pytest mode - default):**
```bash
# MOST PREFERRED: Test failure investigation using file parameter
# Step 1: Create comprehensive debug script
cat > scratch/debug_locals.py << 'EOF'
print("=== Local Variables ===")
for k, v in locals().items():
    if not k.startswith('_'):
        print(f"{k}: {type(v).__name__} = {repr(v)[:100]}")
EOF

# Step 2: Debug production code through the failing test
pydebug-stdin --quiet -f scratch/debug_locals.py src/parser.py 60 -- tests/test_parser.py::test_parse_data -v

# Alternative: Quick inspection with stdin
echo "print(f'Type: {type(parsed_data)}, Contents: {parsed_data}')" | pydebug-stdin --quiet tests/test_parser.py 42
```

**Standalone Python Debugging:**
```bash
# MOST PREFERRED: Debug production CLI through integration tests
# Step 1: Create debug script for CLI
cat > scratch/debug_cli.py << 'EOF'
import json
print("=== CLI Debug Info ===")
if 'args' in locals():
    print(f"Arguments: {vars(args)}")
if 'config' in locals():
    print(f"Config: {json.dumps(config, indent=2)}")
print(f"Local vars: {list(locals().keys())}")
EOF

# Step 2: Debug through CLI integration test
pydebug-stdin --quiet -f scratch/debug_cli.py src/cli_script.py 45 -- tests/test_cli_integration.py::test_production_config -v

# Alternative: Direct debugging when test approach not suitable
echo "print(f'Args: {args}, Config: {config}')" | pydebug-stdin --mode standalone --quiet cli_script.py 45 -- --verbose --config prod.json
```

### Code Quality Standards

- **Formatter**: black (line length 88)
- **Import sorting**: isort
- **Linting**: flake8
- **Type checking**: mypy
- **Auto-fixing**: autoflake

## Testing Requirements

- Use pytest for all testing
- Provide both unit tests and integration tests
- Test both pytest mode and standalone mode functionality
- Include sample projects for comprehensive testing
- No mocks needed - test with real debugging scenarios

## Installation and Setup

The Smart Debugger is designed to be globally accessible:

```bash
# Install dependencies
just install

# Install in development mode
just dev-install

# Test installation
echo 'print("Hello from debugger!")' | pydebug-stdin --help
```

## Configuration

### Environment Variables
```bash
# No special environment variables required
# All configuration is done via command-line flags
```

## Usage Examples

### Debug Test Failures
```bash
# MOST PREFERRED: Debug production code through failing test
# Step 1: Create debug script
cat > scratch/debug_test_failure.py << 'EOF'
print("=== Test Failure Debug ===")
if 'expected' in locals() and 'actual' in locals():
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    print(f"Types: expected={type(expected).__name__}, actual={type(actual).__name__}")
    if expected != actual:
        print("Difference detected!")
else:
    print("Variables 'expected' or 'actual' not found in scope")
    print(f"Available variables: {list(locals().keys())}")
EOF

# Step 2: Debug the production code through the failing test
pydebug-stdin --quiet -f scratch/debug_test_failure.py src/auth.py 125 -- tests/test_auth.py::test_authentication -v

# Alternative: Quick inspection
echo 'print(f"expected={expected}, actual={actual}")' | pydebug-stdin --quiet tests/test_auth.py 25 -- -v
```

### Debug Standalone Scripts
```bash
# MOST PREFERRED: Debug data processing through tests
# Step 1: Create debug script
cat > scratch/debug_data_processing.py << 'EOF'
print("=== Data Processing Debug ===")
if 'data' in locals():
    if hasattr(data, 'shape'):
        print(f"Data shape: {data.shape}")
    if hasattr(data, 'columns'):
        print(f"Columns: {list(data.columns)}")
        print(f"Data types:\n{data.dtypes}")
    if hasattr(data, 'head'):
        print(f"First 5 rows:\n{data.head()}")
else:
    print("Variable 'data' not found")
    print(f"Available: {list(locals().keys())}")
EOF

# Step 2: Debug through integration test
pydebug-stdin --quiet -f scratch/debug_data_processing.py src/process_data.py 80 -- tests/test_data_processing.py::test_csv_processing -v

# Alternative: Direct script debugging
echo 'print(f"data shape: {data.shape}, columns: {list(data.columns)}")' | pydebug-stdin --mode standalone --quiet process_data.py 80 -- input.csv
```

### Debug Python Modules
```bash
# MOST PREFERRED: Debug module through tests
# Step 1: Create debug script
cat > scratch/debug_module_config.py << 'EOF'
import json
print("=== Module Configuration Debug ===")
if 'config' in locals():
    print(f"Config type: {type(config).__name__}")
    if isinstance(config, dict):
        print(f"Environment: {config.get('env', 'not set')}")
        print(f"Full config: {json.dumps(config, indent=2, default=str)}")
    else:
        print(f"Config value: {config}")
else:
    print("Variable 'config' not found")
    print(f"Available: {list(locals().keys())}")
EOF

# Step 2: Debug through module test
pydebug-stdin --quiet -f scratch/debug_module_config.py src/myapp/main.py 30 -- tests/test_main.py::test_production_config -v

# Alternative: Direct module debugging
echo 'print(f"config loaded: {config}")' | pydebug-stdin -m myapp.main --quiet 30 -- --env production
```

## Git and Commit Guidelines

### Commit Message Format
Follow **Conventional Commits (Angular style)**:

- **Format**: `type(scope): description`
- **Reference issues**: Include `Fixes #123` when applicable
- **Types**:
  - **MAJOR/BREAKING**: `type(scope)!:` or include `BREAKING CHANGE:` in footer
  - **MINOR**: `feat:` for feature additions, non-breaking refactors
  - **PATCH**: `fix:`, `docs:`, `style:`, `test:` for bug fixes, documentation, style changes

**Examples**:
```
fix(pydebug): correct module import paths in debugging scripts
feat(debugger): add standalone Python script debugging support  
docs: update CLAUDE.md with commit message guidelines
test: add integration tests for quiet mode functionality
```

### Git Workflow
- **Branching**: Create branches from `main` for features
- **Commits**: Use conventional commit format with clear descriptions
- **Testing**: Always run tests before committing (`just test`)
- **Quality**: Run quality checks before committing (`just quality`)

## Best Practices

### For LLM Agents
- **Always use `-f scratch/debug.py` file parameter** for debugging
- **Always use `--quiet` mode** for clean, minimal output
- **Debug production code through tests** for safety and isolation
- **Write debug scripts to `scratch/` directory** for organization
- **Use JSON formatting** for structured data inspection
- **Prefer test-driven debugging** to isolate and exercise specific code paths

### For Developers
- **Never modify source files** for debugging
- **Use descriptive debug commands** that explain what you're inspecting
- **Leverage Python introspection** capabilities (`type()`, `dir()`, `vars()`)
- **Test both pytest and standalone modes** when developing new features

### For Testing
- **Debug test failures** without modifying test files
- **Inspect test data and fixtures** using the debugger
- **Use with pytest flags** for targeted test execution
- **Verify debugging works** with both simple and complex scenarios

## Troubleshooting

### Common Issues

**Breakpoint Not Hit**
- Verify the line number contains executable code
- Check that the line is actually reached during execution
- For pytest mode: Use `-v` flag to see test execution flow
- For standalone mode: Verify the script runs to that line

**Command Errors**
- Ensure variables exist at the breakpoint location
- Use `locals()` to see available variables
- Check Python syntax in your debug command

**Output Issues**
- Use `--quiet` for clean output
- Check stderr for error messages and warnings
- Ensure proper command structure with stdin method

### Tips
- Start with simple commands like `print(locals())` to see available variables
- Use `type()` and `dir()` to understand object structure
- Leverage `json.dumps()` for complex data visualization
- Always use file parameter (-f) with quiet mode for complex debugging
- Debug production code through tests for safety and reliability
- Use stdin method only for quick one-liners

## Contributing

When contributing to this project:
- Follow the established debugging patterns (use Smart Debugger, not print statements)
- Add tests for new functionality in both pytest and standalone modes
- Update documentation for new features
- Ensure backward compatibility
- Use `just quality` to verify code quality before submitting changes