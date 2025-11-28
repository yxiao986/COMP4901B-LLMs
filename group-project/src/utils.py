def calculate_statistics(numbers):
    """
    Calculates basic statistics for a list of numbers.
    Returns a dictionary with sum, average, max, and min.
    """
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    
    if not numbers:
        return None

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
    - Must contain only alphanumeric characters and underscores.
    - Must not start with a number.
    """
    if not isinstance(username, str):
        return False
        
    if len(username) < 3 or len(username) > 20:
        return False
        
    # Allow alphanumeric characters and underscores
    if not all(c.isalnum() or c == '_' for c in username):
        return False
        
    if username[0].isdigit():
        return False
        
    return True