# utility_tools/hash_generator_logic.py
import hashlib

SUPPORTED_HASH_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512'] # Add more if needed

def generate_hash(text, algorithm='sha256'):
    """
    Generates a hash digest for the input text using the specified algorithm.

    Args:
        text (str): The input text data.
        algorithm (str): The hash algorithm to use (e.g., 'md5', 'sha256').

    Returns:
        str: The hexadecimal hash digest, or None if algorithm is unsupported or error occurs.
    """
    if not isinstance(text, str):
        return None # Input must be a string

    # Ensure algorithm is lowercase and supported
    algorithm = algorithm.lower()
    if algorithm not in SUPPORTED_HASH_ALGORITHMS:
        print(f"[Hash Gen] Error: Unsupported algorithm '{algorithm}'")
        return None

    try:
        # Text must be encoded to bytes before hashing
        text_bytes = text.encode('utf-8') # Use UTF-8 for broad compatibility

        # Create hash object using the specified algorithm
        hasher = hashlib.new(algorithm)

        # Update the hasher with the byte data
        hasher.update(text_bytes)

        # Get the hexadecimal representation of the digest
        hex_digest = hasher.hexdigest()
        print(f"[Hash Gen] Generated {algorithm} hash.")
        return hex_digest

    except Exception as e:
        print(f"Error during hash generation (Algorithm: {algorithm}): {e}")
        import traceback
        traceback.print_exc()
        return None