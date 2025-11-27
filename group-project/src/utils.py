def calculate_statistics(numbers):
    """
    Calculates basic statistics for a list of numbers.
    Returns a dictionary with sum, average, max, and min.
    """
    if not numbers:
        return None
    
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")

    valid_numbers = [n for n in numbers if isinstance(n, (int, float))]
    
    if not valid_numbers:
        return None

    total = sum(valid_numbers)
    count = len(valid_numbers)
    
    return {
        "sum": total,
        "average": total / count,
        "max": max(valid_numbers),
        "min": min(valid_numbers),
        "count": count
    }

def validate_username(username):
    """
    Validates a username.
    Rules:
    - Must be between 3 and 20 characters.
    - Must contain only alphanumeric characters.
    - Must not start with a number.
    """
    if not isinstance(username, str):
        return False
        
    if len(username) < 3 or len(username) > 20:
        return False
        
    if not username.isalnum():
        return False
        
    if username[0].isdigit():
        return False
        
    return True