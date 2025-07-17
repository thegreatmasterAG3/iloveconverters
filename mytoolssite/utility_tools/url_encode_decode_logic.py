# utility_tools/url_encode_decode_logic.py
import urllib.parse

def url_process_text(text, mode='encode'):
    """
    Encodes or decodes text for URL safety (percent-encoding).

    Args:
        text (str): The input text string.
        mode (str): 'encode' or 'decode'.

    Returns:
        tuple: (str: Processed text or None, str: Error message or None)
    """
    if not isinstance(text, str):
        return None, "Input must be text."

    # No need to strip text here, whitespace might be intentional

    try:
        if mode == 'encode':
            # quote_plus encodes spaces as '+' and other special chars
            # safe='' ensures almost all non-alphanumeric chars are encoded
            encoded_text = urllib.parse.quote_plus(text, safe='', encoding='utf-8', errors='strict')
            print("[URL Enc/Dec] Encoded text.")
            return encoded_text, None
        elif mode == 'decode':
            # unquote_plus decodes '+' to space and %XX sequences
            decoded_text = urllib.parse.unquote_plus(text, encoding='utf-8', errors='strict')
            print("[URL Enc/Dec] Decoded text.")
            return decoded_text, None
        else:
            return None, "Invalid mode specified."

    except UnicodeDecodeError:
        print("[URL Enc/Dec] Error: Invalid percent encoding sequence found during decode.")
        return None, "Decoding failed: Invalid percent-encoding sequence found in the input."
    except Exception as e:
        print(f"Error during URL {mode} operation: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred during {mode}ing."