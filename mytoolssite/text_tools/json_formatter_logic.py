# text_tools/json_formatter_logic.py
import json

def format_json_string(input_json_str, indent_style='4', sort_keys=False):
    """
    Formats a JSON string with specified indentation and optional key sorting.

    Args:
        input_json_str (str): The raw JSON string input.
        indent_style (str): '2' for 2 spaces, '4' for 4 spaces, 'tab' for tabs.
        sort_keys (bool): Whether to sort keys alphabetically.

    Returns:
        tuple: (str: Formatted JSON string or None, str: Error message or None)
    """
    if not input_json_str or not isinstance(input_json_str, str):
        return None, "Please enter some JSON data."

    input_json_str = input_json_str.strip()
    if not input_json_str:
         return None, "Input is empty."

    try:
        # Parse the JSON string into a Python object
        data = json.loads(input_json_str)

        # Determine indentation
        indent_value = None
        if indent_style == '4':
            indent_value = 4
        elif indent_style == '2':
            indent_value = 2
        elif indent_style == 'tab':
            indent_value = '\t'
        else: # Default fallback
             indent_value = 4

        # Dump the Python object back into a formatted JSON string
        formatted_json = json.dumps(
            data,
            indent=indent_value,
            sort_keys=sort_keys,
            ensure_ascii=False # Allow unicode characters directly
        )
        print("[JSON Format] Formatting successful.")
        return formatted_json, None # No error

    except json.JSONDecodeError as e:
        print(f"[JSON Format] Invalid JSON input: {e}")
        # Provide a helpful error message including the position
        error_message = f"Invalid JSON: {e.msg} (at line {e.lineno} column {e.colno})"
        return None, error_message
    except Exception as e:
        print(f"Error during JSON formatting: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred: {e}"