# Smart Debugger File Parameter Implementation Plan

## Overview

This plan details how to implement the `-f` file parameter feature for the Smart Debugger. The feature allows users to specify debug commands via a file instead of command-line arguments or stdin piping.

## Example Usage Pattern

```bash
# Write debug commands to a file
echo "print(f'Config: {config}')" > scratch/debug.py

# Use the debug script file with pydebug-stdin
pydebug-stdin --quiet -f scratch/debug.py src/modules/condense.py 150 -- tests/test_integration.py::TestClass::test_method -v
```

### Why This Pattern is Powerful

1. **Separation of Concerns**: Debug commands are separate from the debugging invocation
2. **Complex Commands**: File allows multiline debug scripts without shell escaping issues
3. **Reusability**: Save and reuse debug scripts for common debugging scenarios
4. **Version Control**: Debug scripts can be tracked, shared, and reviewed
5. **Testing Integration**: Run tests that exercise specific code paths while debugging

## Goals

- Add `-f` and `--file` parameter support to both `src/pydebug.py` and `src/pydebug-stdin` wrappers
- Maintain full backward compatibility with existing functionality
- Provide robust error handling for file operations
- Create comprehensive test coverage including the exact usage pattern above
- Update documentation to promote file parameter as preferred method

## Architecture Overview

```
User Input → Wrapper Scripts → smart_debugger CLI → Debugger Classes
     ↓              ↓                   ↓              ↓
-f debug.py    Parse flags        Pass command    Execute at breakpoint
                Read file
```

---

## Phase 1: Architecture Analysis - PREPARATION

**Objective**: Understand the current system before making changes

| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 1.1 | [ ] | Analyze wrapper script structure | Document current argument flow and parsing logic | Map src/pydebug.py and src/pydebug-stdin |
| 1.2 | [ ] | Review existing flag parsing | Understand how --mode, --quiet, -m are handled | Identify insertion point for -f |
| 1.3 | [ ] | Document argument flow | Create diagram of data flow from user to debugger | Include all transformation steps |
| 1.4 | [ ] | Identify integration points | Find where new file reading logic should be added | After flag parsing, before stdin read |

---

## Phase 2: Wrapper Script Updates - IMPLEMENTATION

**Objective**: Add file parameter parsing and reading to both wrapper scripts

### Task 2.1: Update src/pydebug.py wrapper
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 2.1.1 | [ ] | Add -f/--file flag parsing | Both -f and --file work with proper validation | Insert after line 42 (after quiet mode check) |
| 2.1.2 | [ ] | Implement file reading logic | Read command from file with error handling | Handle UTF-8 encoding |
| 2.1.3 | [ ] | Adjust argument count validation | Correct expected args based on -f presence | 2 args if -f, 3 if not |
| 2.1.4 | [ ] | Update usage messages | Clear help text showing both usage patterns | Show -f and non-f examples |

**Implementation Details for 2.1:**
```python
# Location: src/pydebug.py (after line 42)

# Check for -f/--file flag
command_file = None
if '-f' in args:
    f_idx = args.index('-f')
    if f_idx + 1 >= len(args):
        print("Error: -f flag requires a file path", file=sys.stderr)
        return 1
    command_file = args[f_idx + 1]
    args.pop(f_idx)  # Remove -f
    args.pop(f_idx)  # Remove file path
elif '--file' in args:
    f_idx = args.index('--file')
    if f_idx + 1 >= len(args):
        print("Error: --file flag requires a file path", file=sys.stderr)
        return 1
    command_file = args[f_idx + 1]
    args.pop(f_idx)  # Remove --file
    args.pop(f_idx)  # Remove file path

# Validate remaining arguments
if command_file and len(args) < 2:
    print("Usage: pydebug -f <command_file> <file> <line> -- [args]", file=sys.stderr)
    return 1
elif not command_file and len(args) < 3:
    print("Usage: pydebug <file> <line> <command> -- [args]", file=sys.stderr)
    return 1

# File reading logic
if command_file:
    try:
        with open(command_file, 'r', encoding='utf-8') as f:
            command = f.read().strip()
        if not command:
            print(f"Error: Command file {command_file} is empty", file=sys.stderr)
            return 1
    except FileNotFoundError:
        print(f"Error: Command file not found: {command_file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading command file {command_file}: {e}", file=sys.stderr)
        return 1
else:
    command = args[2]
```

### Task 2.2: Update src/pydebug-stdin wrapper
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 2.2.1 | [ ] | Add identical -f/--file parsing | Same logic as pydebug.py | Insert after line 50 (after quiet mode check) |
| 2.2.2 | [ ] | Modify stdin vs file logic | Skip stdin reading when -f provided | File takes precedence over stdin |
| 2.2.3 | [ ] | Update error messages | Consistent "ERROR:" prefix style | Match existing pydebug-stdin style |
| 2.2.4 | [ ] | Update usage and docstring | Show both stdin and file parameter usage | Include example from usage pattern |

### Task 2.3: Update docstrings and help
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 2.3.1 | [ ] | Update pydebug.py docstring | Mention file parameter support | Keep concise |
| 2.3.2 | [ ] | Update pydebug-stdin docstring | Show file parameter examples in usage | Include both methods |
| 2.3.3 | [ ] | Add comprehensive usage messages | Clear examples for all flag combinations | Cover common use cases |

---

## Phase 3: Error Handling and Validation - ROBUSTNESS

**Objective**: Implement comprehensive error handling for file operations

| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 3.1 | [ ] | Handle missing file path | Clear error for -f without argument | "Error: -f flag requires a file path" |
| 3.2 | [ ] | Handle non-existent files | FileNotFoundError with clear message | Include file path in error |
| 3.3 | [ ] | Handle empty files | Detect and error on empty command files | Empty after strip() |
| 3.4 | [ ] | Handle permission errors | PermissionError with helpful message | Guide user to fix permissions |
| 3.5 | [ ] | Handle encoding errors | UnicodeDecodeError with fallback suggestion | Suggest UTF-8 encoding |
| 3.6 | [ ] | Handle large files | Reasonable file size limits | Prevent memory issues |

**Error Handling Patterns:**
```python
# Standard error handling template
try:
    with open(command_file, 'r', encoding='utf-8') as f:
        command = f.read().strip()
    if not command:
        print(f"Error: Command file {command_file} is empty", file=sys.stderr)
        return 1
except FileNotFoundError:
    print(f"Error: Command file not found: {command_file}", file=sys.stderr)
    return 1
except PermissionError:
    print(f"Error: Permission denied reading {command_file}", file=sys.stderr)
    return 1
except UnicodeDecodeError:
    print(f"Error: Invalid encoding in {command_file}. Ensure file is UTF-8", file=sys.stderr)
    return 1
except Exception as e:
    print(f"Error reading command file {command_file}: {e}", file=sys.stderr)
    return 1
```

---

## Phase 4: Comprehensive Testing - VALIDATION

**Objective**: Create thorough test coverage for all functionality and edge cases

### Task 4.1: Basic functionality tests
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 4.1.1 | [ ] | Test pydebug with -f parameter | Command from file executed correctly | Use both pytest and standalone modes |
| 4.1.2 | [ ] | Test pydebug with --file parameter | Long form flag works identically | Same test, different flag |
| 4.1.3 | [ ] | Test pydebug-stdin with -f parameter | File overrides stdin input | No stdin reading |
| 4.1.4 | [ ] | Test complex multiline commands | Elaborate debug scripts work | JSON, loops, imports |
| 4.1.5 | [ ] | Test exact usage pattern | pydebug-stdin --quiet -f scratch/debug.py works | Match user's example |

### Task 4.2: Integration tests
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 4.2.1 | [ ] | Test with --mode standalone | File parameter works with standalone debugging | Script execution |
| 4.2.2 | [ ] | Test with --mode pytest | File parameter works with pytest debugging | Test execution |
| 4.2.3 | [ ] | Test with -m module flag | Module debugging with file commands | Module + file |
| 4.2.4 | [ ] | Test with --quiet flag | Quiet output with file parameter | Clean output |
| 4.2.5 | [ ] | Test with script arguments | File + -- args combination | Full integration |

### Task 4.3: Error handling tests
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 4.3.1 | [ ] | Test missing file path after -f | Clear error message and exit code 1 | "requires a file path" |
| 4.3.2 | [ ] | Test non-existent command file | FileNotFoundError handling | Clear file path in error |
| 4.3.3 | [ ] | Test empty command file | Empty file detection and error | After strip() check |
| 4.3.4 | [ ] | Test permission denied | PermissionError handling | Create unreadable file |
| 4.3.5 | [ ] | Test invalid encoding | UnicodeDecodeError handling | Binary file test |

### Task 4.4: Backward compatibility tests
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 4.4.1 | [ ] | Test existing stdin piping still works | No regression in pydebug-stdin | Original functionality |
| 4.4.2 | [ ] | Test existing direct commands still work | No regression in pydebug.py | Original functionality |
| 4.4.3 | [ ] | Test all existing flags combinations | --mode, --quiet, -m work as before | No interactions |

**Test File Structure:**
```
tests/test_file_parameter.py
├── test_pydebug_with_file_parameter()
├── test_pydebug_with_long_file_parameter()
├── test_pydebug_stdin_with_file_parameter()
├── test_file_parameter_error_cases()
├── test_file_parameter_integration()
├── test_backward_compatibility()
└── test_exact_usage_pattern()  # Tests: pydebug-stdin --quiet -f scratch/debug.py
```

---

## Phase 5: Documentation Updates - COMMUNICATION

**Objective**: Update all documentation to promote file parameter as preferred method

### Task 5.1: Update CLAUDE.md
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 5.1.1 | [ ] | Change preferred method declaration | "-f file parameter" instead of "stdin piping" | Update header |
| 5.1.2 | [ ] | Update basic patterns section | Show -f examples first, stdin as alternative | Clear preference |
| 5.1.3 | [ ] | Update all debugging examples | File parameter examples throughout | Comprehensive coverage |
| 5.1.4 | [ ] | Update benefits section | Explain why file parameter is preferred | Clear advantages |

### Task 5.2: Update README files
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 5.2.1 | [ ] | Update README.md if needed | Add file parameter examples and benefits | Main project README |
| 5.2.2 | [ ] | Update LLM_AGENT_README.md | Comprehensive file parameter guide for LLMs | Technical detail |
| 5.2.3 | [ ] | Update command-line help in scripts | Clear usage examples in --help output | Inline documentation |

### Task 5.3: Update project documentation
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 5.3.1 | [ ] | Add examples to justfile | Create debug-file command example | Show best practices |
| 5.3.2 | [ ] | Update any other relevant docs | Show file parameter examples | Consistency |

---

## Phase 6: Quality Assurance - VERIFICATION

**Objective**: Ensure code quality and comprehensive validation

### Task 6.1: Code quality
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 6.1.1 | [ ] | Run code formatting | just fix on modified files | Use existing justfile commands |
| 6.1.2 | [ ] | Run quality checks | just quality | Includes lint, format, type checking |
| 6.1.3 | [ ] | Run all tests | just test | Ensure no regressions |

### Task 6.2: Manual testing
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 6.2.1 | [ ] | Test basic functionality manually | Quick smoke test of main features | Real usage |
| 6.2.2 | [ ] | Test error cases manually | Verify error messages are helpful | User experience |
| 6.2.3 | [ ] | Test with complex debug scripts | Real-world debugging scenarios | Practical validation |

### Task 6.3: Regression testing
| #   | Status | Task | Success Criteria | Notes |
|-----|--------|------|------------------|-------|
| 6.3.1 | [ ] | Run full test suite | All existing tests pass | No regressions |
| 6.3.2 | [ ] | Test with various Python versions | Feature works across Python 3.8+ | Compatibility |
| 6.3.3 | [ ] | Test file permissions and paths | Works with absolute/relative paths | File system handling |

---

## Implementation Guidelines

### Critical Design Decisions

1. **Argument Parsing Strategy**: Remove `-f` and file path from args list immediately after parsing to maintain clean positional argument handling

2. **File Reading Strategy**: Use UTF-8 encoding explicitly and comprehensive error handling

3. **Precedence Rules**: File parameter takes precedence over stdin in pydebug-stdin

4. **Error Message Format**: Consistent formatting between wrappers with clear, actionable messages

5. **Backward Compatibility**: Zero changes to existing behavior when `-f` not used

### Code Style Guidelines

```python
# Consistent error handling pattern
def read_command_file(command_file: str) -> tuple[str, int]:
    """Read command from file with comprehensive error handling.
    
    Returns:
        (command_content, exit_code) - command on success, ("", 1) on error
    """
    try:
        with open(command_file, 'r', encoding='utf-8') as f:
            command = f.read().strip()
        if not command:
            print(f"Error: Command file {command_file} is empty", file=sys.stderr)
            return "", 1
        return command, 0
    except FileNotFoundError:
        print(f"Error: Command file not found: {command_file}", file=sys.stderr)
        return "", 1
    except Exception as e:
        print(f"Error reading command file {command_file}: {e}", file=sys.stderr)
        return "", 1
```

### Testing Strategy

1. **Test Structure**: Separate test file `test_file_parameter.py` with comprehensive coverage
2. **Test Data**: Use `tempfile.TemporaryDirectory()` for isolated test environments
3. **Error Testing**: Test each error condition explicitly with expected error messages
4. **Integration Testing**: Test all flag combinations to ensure no conflicts

### Common Pitfalls to Avoid

1. **Don't forget to remove parsed flags** from args list before positional parsing
2. **Handle empty files explicitly** - distinguish from FileNotFoundError
3. **Use proper file encoding** - UTF-8 to handle international characters
4. **Test edge cases** - very long files, special characters, binary files
5. **Maintain error message consistency** between both wrapper scripts

### Example Test Case for Exact Usage Pattern

```python
def test_exact_usage_pattern(tmp_path):
    """Test the exact usage pattern from the requirements."""
    # Create a debug script file
    debug_file = tmp_path / "scratch" / "debug.py"
    debug_file.parent.mkdir(exist_ok=True)
    debug_file.write_text('print(f"Config: {config}")')
    
    # Create a test file to debug
    test_file = tmp_path / "src" / "modules" / "condense.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text('''
def process_config(config):
    # Line 150 would be here in real file
    result = config.get('value', 'default')
    return result
''')
    
    # Run the exact command pattern
    result = subprocess.run([
        'pydebug-stdin', '--quiet', '-f', str(debug_file),
        str(test_file), '150', '--',
        'tests/test_integration.py::TestClass::test_method', '-v'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Config:" in result.stdout
```

---

## Success Criteria

### Functional Requirements
- [ ] `-f filename` works in both pydebug.py and pydebug-stdin
- [ ] `--file filename` works identically to `-f`
- [ ] File parameter integrates with all existing flags
- [ ] Clear error messages for all failure cases
- [ ] Backward compatibility maintained 100%

### Quality Requirements
- [ ] 100% test coverage for new functionality
- [ ] All existing tests continue to pass
- [ ] Code style consistent with existing codebase
- [ ] Documentation updated comprehensively

### User Experience Requirements
- [ ] File parameter promoted as preferred method in docs
- [ ] Clear examples provided for common use cases
- [ ] Error messages guide users to correct usage
- [ ] Feature is discoverable through help text

## Timeline Estimate

- **Phase 1 (Analysis)**: 30 minutes (architecture is well understood)
- **Phase 2 (Implementation)**: 2-3 hours  
- **Phase 3 (Error Handling)**: 1-2 hours
- **Phase 4 (Testing)**: 3-4 hours
- **Phase 5 (Documentation)**: 1-2 hours
- **Phase 6 (QA)**: 1 hour

**Total Estimated Time**: 8-12 hours

This plan provides a comprehensive roadmap for implementing the `-f` file parameter feature while maintaining code quality, backward compatibility, and thorough documentation.