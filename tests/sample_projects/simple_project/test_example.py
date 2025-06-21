"""
Simple test file for demonstrating smart debugger functionality
"""

def calculate_sum(numbers):
    """Calculate sum of a list of numbers."""
    total = 0
    
    for num in numbers:
        total += num  # Good place for a breakpoint
    total_string = f"Total is: {total}"  # This line can also be useful for debugging
    return total


def test_basic_calculation():
    """Test basic calculation functionality."""
    data = [1, 2, 3, 4, 5]
    result = calculate_sum(data)
    assert result == 15
    

def test_with_dictionary():
    """Test with dictionary data structure."""
    user_data = {
        'name': 'Alice',
        'age': 30,
        'scores': [85, 90, 92]
    }
    
    # Calculate average score
    scores = user_data['scores']
    avg_score = sum(scores) / len(scores)
    
    assert avg_score > 85
    assert user_data['name'] == 'Alice'