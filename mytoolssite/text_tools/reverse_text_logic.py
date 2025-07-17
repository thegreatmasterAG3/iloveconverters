# text_tools/reverse_text_logic.py
import re

def reverse_text_logic(text, mode='string'):
    """
    Reverses text based on the selected mode.

    Args:
        text (str): The input text.
        mode (str): 'string' (default), 'words', 'word_order'.

    Returns:
        str: The reversed text.
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()
    if not text:
        return ""

    try:
        if mode == 'words':
            # Reverse each word individually, preserving whitespace between them
            # Use regex to find words and non-words (whitespace/punctuation)
            parts = re.split(r'(\s+)', text) # Split keeping delimiters
            reversed_parts = [part[::-1] if part.strip() else part for part in parts]
            return "".join(reversed_parts)

        elif mode == 'word_order':
            # Reverse the order of words, keeping original whitespace count roughly
            words = text.split()
            return " ".join(words[::-1]) # Simple space join

        elif mode == 'string': # Default
            # Reverse the entire string
            return text[::-1]

        else: # Unknown mode
            return text[::-1] # Default to full string reverse

    except Exception as e:
        print(f"Error during text reversal (mode: {mode}): {e}")
        return text # Return original on error