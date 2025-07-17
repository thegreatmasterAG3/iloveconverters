# text_tools/text_cleaner_logic.py
import re

def clean_text_data(text, options=None):
    """
    Cleans text based on selected options.

    Args:
        text (str): The input text.
        options (dict): Dictionary of boolean cleaning options, e.g.,
                        {'remove_extra_spaces': True, 'remove_line_breaks': False, ...}

    Returns:
        str: The cleaned text, or the original text if no options selected/error.
    """
    if not text or not isinstance(text, str):
        return text # Return original if empty or not string

    if options is None:
        options = {}

    cleaned_text = text
    print(f"[Text Cleaner Logic] Starting cleaning with options: {options}")

    # --- Apply cleaning steps based on options ---

    # 1. Trim Each Line (Applied first often makes other steps cleaner)
    if options.get('trim_lines'):
        print("  Applying: Trim Lines")
        lines = cleaned_text.splitlines()
        cleaned_text = '\n'.join(line.strip() for line in lines)

    # 2. Remove HTML Tags (Basic - might not handle complex/broken HTML well)
    if options.get('remove_html'):
        print("  Applying: Remove HTML Tags")
        # Regex to remove anything between < and >
        clean_re = re.compile('<.*?>')
        cleaned_text = re.sub(clean_re, '', cleaned_text)

    # 3. Remove Empty Lines (Lines containing only whitespace after potential trim/HTML removal)
    if options.get('remove_empty_lines'):
        print("  Applying: Remove Empty Lines")
        lines = cleaned_text.splitlines()
        # Keep lines that are not empty after stripping whitespace again
        cleaned_text = '\n'.join(line for line in lines if line.strip())

    # 4. Remove Extra Spaces (leading/trailing overall, multiple internal spaces)
    if options.get('remove_extra_spaces'):
        print("  Applying: Remove Extra Spaces")
        # Remove leading/trailing whitespace from the whole string
        cleaned_text = cleaned_text.strip()
        # Replace multiple whitespace characters (including space, tab, newline if not removed yet) with a single space
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    # 5. Remove ALL Line Breaks (Applied last if selected, overrides remove_empty_lines/trim)
    if options.get('remove_all_line_breaks'):
        print("  Applying: Remove All Line Breaks")
        # Replace any newline characters (\n, \r) with a space, then clean extra spaces again
        cleaned_text = cleaned_text.replace('\n', ' ').replace('\r', '')
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()


    print("[Text Cleaner Logic] Cleaning finished.")
    return cleaned_text