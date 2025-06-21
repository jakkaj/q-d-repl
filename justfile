# Smart Debugger Justfile
# Standalone build commands for the project-agnostic pytest debugger

# Default recipe - show available commands
default:
    @just --list

# Install debugger dependencies
install:
    pip3 install -r requirements.txt

# Run debugger tests
test:
    python3 -m pytest tests/ -v

# Run only unit tests
test-unit:
    python3 -m pytest tests/ -v -m unit

# Run integration tests
test-integration:
    python3 -m pytest tests/test_integration.py -v

# Debug any test file at specific line
debug-test file line command="":
    python3 -m smart_debugger {{file}} {{line}} "{{command}}" -- -v -s

# Example debugging session - show total_string value
debug-example:
    python3 -m smart_debugger \
        tests/sample_projects/simple_project/test_example.py \
        11 \
        "print(f'Debug: total_string={total_string}')" \
        -- \
        -v -s

# Example debugging in a loop
debug-loop:
    python3 -m smart_debugger \
        tests/sample_projects/simple_project/test_example.py \
        10 \
        "print(f'Debug: total={total}, num={num}')" \
        -- \
        -v -s

# Format code
format:
    black smart_debugger tests examples
    isort smart_debugger tests examples

# Lint code
lint:
    flake8 smart_debugger tests examples
    mypy smart_debugger tests examples

# Fix common issues
fix:
    autoflake --remove-all-unused-imports --recursive --in-place smart_debugger tests examples
    isort smart_debugger tests examples
    black smart_debugger tests examples

# Run all quality checks
quality: format lint test

# Clean up generated files
clean:
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -delete
    find . -name ".pytest_cache" -delete -type d
    find . -name ".mypy_cache" -delete -type d

# Install in development mode
dev-install:
    pip3 install -e .

# Create a simple test file for debugging examples
create-test-example:
    mkdir -p tests/sample_projects/simple_project
    echo "def test_example():\n    data = {'key': 'value', 'numbers': [1, 2, 3]}\n    assert data['key'] == 'value'" > tests/sample_projects/simple_project/test_example.py