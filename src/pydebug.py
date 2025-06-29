#!/usr/bin/env python3
"""
Smart debugger wrapper that handles multiline commands properly.

Usage:
    pydebug [--mode MODE] [--quiet|-q] [-m] <file> <line> <command> -- [args]
    pydebug [--mode MODE] [--quiet|-q] [-m] -f <command_file> <file> <line> -- [args]

Examples:
    # Direct command
    pydebug test.py 42 "print(x)" -- -v

    # Command from file
    pydebug -f debug_script.py test.py 42 -- -v
"""
import os
import subprocess
import sys


def main():
    # Parse arguments
    args = sys.argv[1:]

    # Check for --mode flag
    mode = "pytest"  # Default mode
    mode_idx = -1
    for i, arg in enumerate(args):
        if arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            mode_idx = i
            break

    if mode_idx >= 0:
        # Remove --mode and its value
        args.pop(mode_idx)  # Remove --mode
        args.pop(mode_idx)  # Remove the mode value

    # Check for -m flag (module mode) in standalone
    is_module = False
    if mode == "standalone" and "-m" in args:
        is_module = True
        args.remove("-m")

    # Check for --quiet/-q flag
    quiet_mode = False
    if "--quiet" in args:
        quiet_mode = True
        args.remove("--quiet")
    elif "-q" in args:
        quiet_mode = True
        args.remove("-q")

    # Check for -f/--file flag
    command_file = None
    if "-f" in args:
        f_idx = args.index("-f")
        if f_idx + 1 >= len(args):
            print("Error: -f flag requires a file path", file=sys.stderr)
            return 1
        command_file = args[f_idx + 1]
        args.pop(f_idx)  # Remove -f
        args.pop(f_idx)  # Remove file path
    elif "--file" in args:
        f_idx = args.index("--file")
        if f_idx + 1 >= len(args):
            print("Error: --file flag requires a file path", file=sys.stderr)
            return 1
        command_file = args[f_idx + 1]
        args.pop(f_idx)  # Remove --file
        args.pop(f_idx)  # Remove file path

    # Validate remaining arguments
    if command_file and len(args) < 2:
        print(
            "Usage: pydebug [--mode MODE] [--quiet|-q] [-m] -f <command_file> "
            "<file> <line> -- [args]",
            file=sys.stderr,
        )
        return 1
    elif not command_file and len(args) < 3:
        print(
            "Usage: pydebug [--mode MODE] [--quiet|-q] [-m] <file> <line> <command> -- [args]",
            file=sys.stderr,
        )
        print(
            "   OR: pydebug [--mode MODE] [--quiet|-q] [-m] -f <command_file> <file> <line> -- [args]",
            file=sys.stderr,
        )
        print("Modes: pytest (default), standalone", file=sys.stderr)
        return 1

    file_path = args[0]
    line_no = args[1]

    # Read command from file or argument
    if command_file:
        try:
            with open(command_file, "r", encoding="utf-8") as f:
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
            print(
                f"Error: Invalid encoding in {command_file}. Ensure file is UTF-8",
                file=sys.stderr,
            )
            return 1
        except Exception as e:
            print(f"Error reading command file {command_file}: {e}", file=sys.stderr)
            return 1
    else:
        command = args[2]

    # Convert relative path to absolute
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    # Find the -- separator
    extra_args = []
    if "--" in args:
        sep_index = args.index("--")
        extra_args = args[sep_index + 1 :]

    # Handle multiline commands properly
    # The issue is that when pasting multiline commands in terminal,
    # the indentation might get messed up. We need to be smarter about this.

    # First, let's see if this looks like a multiline string that got mangled
    if "\n" in command and ('"""' in command or "'''" in command):
        # This is likely a multiline string literal
        # The problem is that the terminal might have added indentation
        # Let's try to fix it by removing any leading whitespace from continuation lines

        lines = command.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            if i == 0:
                # First line - keep as is
                fixed_lines.append(line)
            else:
                # Subsequent lines - if they start with whitespace and we're inside a string,
                # they might be incorrectly indented
                # Check if we're likely inside a multiline string
                if any(marker in "".join(fixed_lines) for marker in ['"""', "'''"]):
                    # We're probably inside a string - strip leading whitespace
                    fixed_lines.append(line.lstrip())
                else:
                    fixed_lines.append(line)

        cleaned_command = "\n".join(fixed_lines)
    else:
        # Single line or non-string multiline - use as-is
        cleaned_command = command

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Build the command
    cmd = [sys.executable, "-m", "smart_debugger"]

    # Add mode flag if not default
    if mode != "pytest":
        cmd.extend(["--mode", mode])

    # Add quiet flag
    if quiet_mode:
        cmd.append("--quiet")

    # Add module flag if needed
    if is_module:
        cmd.append("-m")

    # Add positional arguments
    cmd.extend([file_path, line_no, cleaned_command])

    # Add extra arguments
    if extra_args:
        cmd.extend(["--"] + extra_args)

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    src_path = os.path.join(project_root, "src")
    existing_path = env.get("PYTHONPATH", "")
    if existing_path:
        env["PYTHONPATH"] = f"{src_path}:{existing_path}"
    else:
        env["PYTHONPATH"] = src_path

    # Run the command
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    sys.exit(main())
