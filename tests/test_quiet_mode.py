"""Test for quiet mode."""

def test_quiet():
    """Simple test for quiet mode."""
    x = 42
    y = 100
    print(f"Before breakpoint: x={x}, y={y}")
    # Breakpoint will be here at line 8
    total = x + y
    print(f"After breakpoint: total={total}")
    assert total == 142