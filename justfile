# Smart Debugger Justfile
# Standalone build commands for the project-agnostic pytest debugger

# Default recipe - show available commands
default:
    @just --list

# Install debugger dependencies
install:
    pip3 install -r requirements.txt --break-system-packages

# === Substrate CLI Development Tasks ===
# Run `just --list` to see all available commands


fft: format fix test

# === Code Quality ===
ff: format fix

# Format code automatically (like dart format)
format:
    black ./src tests/
    isort ./src tests/

# Fix code issues automatically (like dart fix)
fix:
    autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive ./src tests/
    isort ./src tests/
    black ./src tests/

# Run linting checks
lint:
    flake8 ./src tests/ --max-line-length=88 --ignore=E203,W503,F401,F403,F841,E402
    black --check ./src tests/
    isort --check-only ./src tests/

# Run type checking
typecheck:
    mypy ./src --config-file pyproject.toml

# Run debugger tests
test:
    PYTHONPATH=src python3 -m pytest tests/ -v

# Run only unit tests
test-unit:
    PYTHONPATH=src python3 -m pytest tests/ -v -m unit

# Run integration tests
test-integration:
    PYTHONPATH=src python3 -m pytest tests/test_integration.py -v

# Debug any test file at specific line
debug-test file line command="":
    PYTHONPATH=src python3 -m smart_debugger {{file}} {{line}} "{{command}}" -- -v -s

# Example debugging session - show total_string value
debug-example:
    PYTHONPATH=src python3 -m smart_debugger \
        tests/sample_projects/simple_project/test_example.py \
        11 \
        "print(f'Debug: total_string={total_string}')" \
        -- \
        -v -s

# Example debugging in a loop
debug-loop:
    PYTHONPATH=src python3 -m smart_debugger \
        tests/sample_projects/simple_project/test_example.py \
        11 \
        "print(f'Debug: total={total}, num={num}')" \
        -- \
        -v -s

# Example debugging with file parameter
debug-file:
    echo "print(f'Debug: total_string={total_string}')" > scratch/debug_cmd.py
    PYTHONPATH=src python3 src/pydebug-stdin -f scratch/debug_cmd.py --quiet \
        tests/sample_projects/simple_project/test_example.py \
        11 \
        -- \
        -v -s

clean:
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -delete
    find . -name ".pytest_cache" -delete -type d
    find . -name ".mypy_cache" -delete -type d

# Install in development mode
dev-install:
    pip3 install -e .

# Update GitHub issue with plan content
update-issue issue_number title plan_path:
    @echo "📝 Updating GitHub issue #{{issue_number}} with {{plan_path}}..."
    PAGER=cat gh issue edit {{issue_number}} --title "{{title}}" --body-file {{plan_path}}
    @echo "✅ Issue #{{issue_number}} updated successfully"

# Get GitHub issue details
get-issue issue_number:
    @echo "📋 Fetching GitHub issue #{{issue_number}}..."
    PAGER=cat gh issue view {{issue_number}}

update-claude:
    npm update -g @anthropic-ai/claude-code