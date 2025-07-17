# utility_tools/password_generator_logic.py
import secrets
import string

def generate_password(length=16, include_uppercase=True, include_lowercase=True, include_numbers=True, include_symbols=True):
    """
    Generates a random password based on specified criteria.

    Args:
        length (int): Desired password length.
        include_uppercase (bool): Include uppercase letters.
        include_lowercase (bool): Include lowercase letters.
        include_numbers (bool): Include digits.
        include_symbols (bool): Include punctuation/symbols.

    Returns:
        str: The generated password, or None if no character sets are selected.
    """
    # Define character sets
    letters_upper = string.ascii_uppercase
    letters_lower = string.ascii_lowercase
    digits = string.digits
    # Define a good set of common symbols
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Build the pool of allowed characters
    character_pool = ""
    guaranteed_chars = [] # To ensure at least one of each selected type

    if include_uppercase:
        character_pool += letters_upper
        guaranteed_chars.append(secrets.choice(letters_upper))
    if include_lowercase:
        character_pool += letters_lower
        guaranteed_chars.append(secrets.choice(letters_lower))
    if include_numbers:
        character_pool += digits
        guaranteed_chars.append(secrets.choice(digits))
    if include_symbols:
        character_pool += symbols
        guaranteed_chars.append(secrets.choice(symbols))

    # Check if at least one character set was selected
    if not character_pool:
        return None # Cannot generate password with no characters

    # Ensure length is reasonable (adjust min/max as needed)
    length = max(4, min(length, 128)) # Ensure at least 4, max 128

    # Ensure the length is at least the number of guaranteed characters
    if length < len(guaranteed_chars):
        length = len(guaranteed_chars) # Force minimum length if needed

    # Generate the remaining characters needed
    remaining_length = length - len(guaranteed_chars)
    password_chars = guaranteed_chars + [secrets.choice(character_pool) for _ in range(remaining_length)]

    # Shuffle the characters to avoid predictable patterns (e.g., symbols always at end)
    secrets.SystemRandom().shuffle(password_chars) # Use SystemRandom for better shuffle

    return "".join(password_chars)