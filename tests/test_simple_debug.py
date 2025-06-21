"""Very simple test for debugging."""


def test_basic():
    """Simplest possible test."""
    x = 10
    y = 20
    # Line 7 - breakpoint here
    result = x + y
    assert result == 30
    print(f"Test passed: {x} + {y} = {result}")
