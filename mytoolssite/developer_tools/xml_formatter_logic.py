# developer_tools/xml_formatter_logic.py
import xml.dom.minidom
import xml.parsers.expat # For catching specific parsing errors

def format_xml_string(xml_string, indent_choice='4s'):
    """
    Formats (pretty-prints) an XML string.

    Args:
        xml_string (str): The raw XML input.
        indent_choice (str): '2s' (2 spaces), '4s' (4 spaces), 'tab'.

    Returns:
        tuple: (str: formatted XML or None, str: error message or None)
    """
    if not xml_string or not isinstance(xml_string, str):
        return None, "No XML input provided."

    xml_string = xml_string.strip()
    if not xml_string:
        return None, "XML input is empty."

    # Determine indentation string
    if indent_choice == '2s':
        indent_str = "  "
    elif indent_choice == 'tab':
        indent_str = "\t"
    else: # Default to 4 spaces
        indent_str = "    "

    try:
        # Parse the XML string
        dom = xml.dom.minidom.parseString(xml_string)

        # Pretty print using toprettyxml
        # newl='\n' prevents extra blank lines sometimes added
        pretty_xml = dom.toprettyxml(indent=indent_str, newl='\n')

        # Remove the initial XML declaration <?xml ...?> added by toprettyxml
        # Split lines, filter out the first line if it's the declaration, rejoin
        lines = pretty_xml.splitlines()
        if lines and lines[0].strip().startswith('<?xml'):
            formatted_xml = '\n'.join(lines[1:]).strip()
        else:
            formatted_xml = pretty_xml.strip()

        # Further cleanup: Remove empty lines that might remain
        formatted_xml = '\n'.join(line for line in formatted_xml.splitlines() if line.strip())

        print("[XML Format Logic] Formatting successful.")
        return formatted_xml, None # Success

    except xml.parsers.expat.ExpatError as e:
        error_message = f"Invalid XML: Error on line {e.lineno}, column {e.offset}. Details: {e.code}"
        print(f"[XML Format Logic] {error_message}")
        return None, error_message
    except Exception as e:
        print(f"Error during XML formatting: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred during formatting: {e}"