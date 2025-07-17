# utility_tools/random_number_logic.py
import random

def generate_random_integers(min_val, max_val, count=1):
    """
    Generates a specified count of random integers within a range.

    Args:
        min_val (int): The minimum possible integer value.
        max_val (int): The maximum possible integer value.
        count (int): How many random integers to generate.

    Returns:
        list: A list of generated random integers, or None if inputs are invalid.
              Returns an empty list if count is 0.
    """
    # Basic validation (more robust in view)
    if not isinstance(min_val, int) or not isinstance(max_val, int) or not isinstance(count, int):
        print("[Random Num Logic] Error: Inputs must be integers.")
        return None
    if min_val > max_val:
        print("[Random Num Logic] Error: Minimum value cannot be greater than maximum value.")
        return None
    if count < 0:
        print("[Random Num Logic] Error: Count cannot be negative.")
        return None
    if count == 0:
        return []

    print(f"[Random Num Logic] Generating {count} numbers between {min_val} and {max_val}")
    results = []
    try:
        for _ in range(count):
            results.append(random.randint(min_val, max_val))
        print(f"[Random Num Logic] Generated: {results}")
        return results
    except Exception as e:
        # Should be unlikely with randint if inputs are valid ints and min <= max
        print(f"Error during random number generation: {e}")
        return None