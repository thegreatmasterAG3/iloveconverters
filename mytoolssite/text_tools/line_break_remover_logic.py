# text_tools/line_break_remover_logic.py
import re

def process_line_breaks(text, mode='remove_all'):
    """
    Removes or modifies line breaks in text based on the selected mode.

    Args:
        text (str): The input text string.
        mode (str): 'remove_all', 'remove_empty', or 'replace_with_space'.

    Returns:
        str: The processed text string, or the original text if input is invalid/empty.
    """
    if not text or not isinstance(text, str):
        return text or "" # Return empty string if input is None or not string

    # Normalize line endings (\r\n and \r -> \n)
    normalized_text = text.replace('\r\n', '\n').replace('\r', '\n')

    if mode == 'remove_all':
        # Remove all newline characters
        result = normalized_text.replace('\n', '')
        print("[Line Break] Mode: Remove All")

    elif mode == 'remove_empty':
        # Remove lines containing only whitespace, keep single newlines
        lines = normalized_text.split('\n')
        # Keep lines that are not empty after stripping whitespace
        non_empty_lines = [line for line in lines if line.strip()]
        result = '\n'.join(non_empty_lines)
        print("[Line Break] Mode: Remove Empty Lines")

    elif mode == 'replace_with_space':
        # Replace single newlines with a space, collapse multiple newlines to one space
        # First, replace multiple newlines with a single one
        text_single_newlines = re.sub(r'\n+', '\n', normalized_text)
        # Then replace remaining newlines with spaces
        result = text_single_newlines.replace('\n', ' ')
        print("[Line Break] Mode: Replace with Space")

    else: # Default or unknown mode, return normalized
        result = normalized_text
        print("[Line Break] Mode: Unknown/Default (Normalized)")

    return result.strip() # Trim leading/trailing whitespace from final result