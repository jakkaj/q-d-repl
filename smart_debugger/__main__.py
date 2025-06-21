#!/usr/bin/env python3
"""
Smart Debugger - Non-interactive pytest debugging for LLM agents.

Usage:
    python3 -m smart_debugger <file> <line> "<command>" -- [pytest_args]
"""

import sys
from pathlib import Path


def main():
    """Main entry point for smart debugger."""
    # Always show version banner
    print("Smart Debugger v1.2.0 - Non-interactive debugging for LLM agents", file=sys.stderr)
    
    args = sys.argv[1:]
    
    # Check for --quiet flag
    quiet_mode = False
    if '--quiet' in args:
        quiet_mode = True
        args.remove('--quiet')
    elif '-q' in args:
        quiet_mode = True
        args.remove('-q')
    
    # Check for --mode flag
    mode = 'pytest'  # Default mode
    mode_idx = -1
    for i, arg in enumerate(args):
        if arg == '--mode' and i + 1 < len(args):
            mode = args[i + 1]
            mode_idx = i
            break
    
    if mode_idx >= 0:
        # Remove --mode and its value
        args.pop(mode_idx)  # Remove --mode
        args.pop(mode_idx)  # Remove the mode value
    
    # Validate mode
    if mode not in ['pytest', 'standalone']:
        print(f"Error: Invalid mode '{mode}'. Must be 'pytest' or 'standalone'", file=sys.stderr)
        return 1
    
    # Check for -m flag (module mode) in standalone
    is_module = False
    if mode == 'standalone' and '-m' in args:
        is_module = True
        args.remove('-m')
    
    # Parse arguments
    if len(args) < 3:
        if not quiet_mode:
            print("Usage: python3 -m smart_debugger [--quiet|-q] [--mode MODE] <file> <line> <command> [-- args]", file=sys.stderr)
            print("Modes: pytest (default), standalone", file=sys.stderr)
            print("Examples:", file=sys.stderr)
            print("  python3 -m smart_debugger test.py 10 \"print(x)\" -- -v", file=sys.stderr)
            print("  python3 -m smart_debugger --quiet test.py 10 \"print(x)\" -- -v", file=sys.stderr)
            print("  python3 -m smart_debugger --mode standalone script.py 42 \"print(sys.argv)\" -- arg1 arg2", file=sys.stderr)
        return 1
    
    file_path = args[0]
    try:
        line_no = int(args[1])
    except ValueError:
        if not quiet_mode:
            print(f"Error: Invalid line number: {args[1]}", file=sys.stderr)
        return 1
    
    command = args[2]
    
    # Split pytest args if present
    if '--' in args:
        sep_index = args.index('--')
        pytest_args = args[sep_index + 1:]
    else:
        pytest_args = []
    
    # Validate file exists (only for non-module standalone and pytest modes)
    if not (mode == 'standalone' and is_module) and not Path(file_path).exists():
        if not quiet_mode:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    
    # Run the appropriate debugger based on mode
    if mode == 'pytest':
        from .non_interactive import run_non_interactive_debug
        exit_code = run_non_interactive_debug(file_path, line_no, command, pytest_args, quiet_mode)
    else:  # standalone mode
        from .standalone import run_standalone_debug
        exit_code = run_standalone_debug(file_path, line_no, command, pytest_args, quiet_mode, is_module)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())