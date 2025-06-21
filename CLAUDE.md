# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL: Debugging Requirements

**NEVER insert debug outputs directly into code!** Always use the Smart Debugger for debugging ANY Python code:
- ❌ **DO NOT** add `print()` statements to source files for debugging
- ❌ **DO NOT** insert `import pdb; pdb.set_trace()` or similar debugger calls
- ❌ **DO NOT** modify test files with debug output
- ❌ **DO NOT** run debug commands from terminal like `python3 -m pdb`
- ✅ **ALWAYS** use `pydebug-stdin` with stdin piping for reliable debugging
- ✅ **ALWAYS** use the `--quiet` flag to minimize output for LLM agents
- ✅ **SUPPORTS** both pytest tests and standalone Python scripts/modules

### How to Debug Tests and Code

**PREFERRED METHOD**: Use `pydebug-stdin` with stdin piping for maximum reliability and flexibility.

**Basic Pattern:**
```bash
echo "command" | pydebug-stdin [--mode MODE] --quiet file.py line_number
```

**Debugging Tests (default mode):**
```bash
# Simple variable inspection in a test
echo "print(variable_name)" | pydebug-stdin --quiet /path/to/test_file.py 42

# Complex expressions in test context
echo "print(f'Type: {type(data)}, Value: {data}')" | pydebug-stdin --quiet tests/test_example.py 60
```

**Debugging Standalone Python Scripts:**
```bash
# Debug a standalone Python script
echo "print(config)" | pydebug-stdin --mode standalone --quiet /path/to/script.py 42

# Debug with script arguments
echo "print(sys.argv)" | pydebug-stdin --mode standalone --quiet script.py 10 -- --arg1 value1

# Debug a Python module
echo "print(locals())" | pydebug-stdin --mode standalone -m mymodule --quiet 30

# JSON-formatted output for structured data
echo "import json; print(json.dumps(result_dict, indent=2))" | pydebug-stdin --mode standalone --quiet src/module.py 75
```

**Why stdin method is preferred:**
- Handles multiline commands reliably without shell escaping issues
- Avoids terminal line-wrapping problems with long expressions
- Better for complex expressions and JSON formatting
- More robust and predictable for LLM agent usage
- Eliminates quoting and escaping complexities
- Works with ANY Python code: tests, scripts, modules, packages

The `pydebug-stdin` tool will:
- Set breakpoints automatically at the specified line
- Execute your piped commands at the breakpoint
- Return clean output with `--quiet` mode
- Exit cleanly without requiring interaction
- Support both pytest test debugging and standalone Python debugging

#### Stdin Method with Quiet Mode (Preferred for LLM Agents)

**IMPORTANT**: LLM agents should ALWAYS use `pydebug-stdin --quiet` by default to save context space and ensure reliable command execution.

**Basic stdin pattern with quiet mode:**
```bash
echo "print(variable_name)" | pydebug-stdin --quiet file.py line_number
```

**Advanced stdin examples:**
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

For 99% of debugging tasks, `pydebug-stdin --quiet` provides all necessary information while conserving valuable token space.

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
echo "print(variable)" | pydebug-stdin --quiet tests/test_file.py 42 -- -v
```

## File Structure

### Core Components
- `smart_debugger/` - Main debugger package
  - `__main__.py` - CLI entry point
  - `non_interactive.py` - Core debugging logic
  - `standalone.py` - Standalone Python script support
- `pydebug` - Global command wrapper
- `pydebug-stdin` - Stdin-based command wrapper (preferred)
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

# ✅ CORRECT - Use pydebug-stdin with stdin piping:
echo "print(f'result={result}')" | pydebug-stdin --quiet src/my_module.py 45
```

#### Common Debugging Scenarios

**Test Debugging (pytest mode - default):**
```bash
# Test failure investigation
echo "print({k: type(v).__name__ for k, v in locals().items() if not k.startswith('_')})" | pydebug-stdin --quiet tests/test_example.py 60

# Data structure analysis in tests
echo "print(f'Type: {type(parsed_data)}, Contents: {parsed_data}')" | pydebug-stdin --quiet tests/test_parser.py 42
```

**Standalone Python Debugging:**
```bash
# Debug a CLI script
echo "print(f'Args: {args}, Config: {config}')" | pydebug-stdin --mode standalone --quiet cli_script.py 45 -- --verbose --config prod.json

# Debug a Python module
echo "import json; print(json.dumps(module_state, indent=2))" | pydebug-stdin --mode standalone -m mypackage.module --quiet 30
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
# Inspect failing test variables
echo 'print(f"expected={expected}, actual={actual}")' | pydebug-stdin --quiet tests/test_auth.py 25 -- -v
```

### Debug Standalone Scripts
```bash
# Debug data processing script
echo 'print(f"data shape: {data.shape}, columns: {list(data.columns)}")' | pydebug-stdin --mode standalone --quiet process_data.py 80 -- input.csv
```

### Debug Python Modules
```bash
# Debug module execution
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
- **Always use `--quiet` mode** for clean, minimal output
- **Prefer `pydebug-stdin`** over direct command for reliability
- **Use JSON formatting** for structured data inspection
- **Combine multiple statements** with semicolons when needed

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
- Always use stdin method with quiet mode for LLM efficiency

## Contributing

When contributing to this project:
- Follow the established debugging patterns (use Smart Debugger, not print statements)
- Add tests for new functionality in both pytest and standalone modes
- Update documentation for new features
- Ensure backward compatibility
- Use `just quality` to verify code quality before submitting changes