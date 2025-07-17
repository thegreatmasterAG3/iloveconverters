# utility_tools/base64_logic.py
import base64

def process_base64(text, mode='encode', encoding='utf-8'):
    """
    Encodes text to Base64 or decodes Base64 back to text.

    Args:
        text (str): The input text string (plain or base64).
        mode (str): 'encode' or 'decode'.
        encoding (str): The text encoding to use (e.g., 'utf-8').

    Returns:
        tuple: (str: Processed text or None, str: Error message or None)
    """
    if not isinstance(text, str):
        return None, "Input must be text."
    # No strip needed initially

    try:
        if mode == 'encode':
            text_bytes = text.encode(encoding)
            base64_bytes = base64.b64encode(text_bytes)
            result_text = base64_bytes.decode(encoding) # Decode result bytes back to string
            print("[Base64] Encoded text.")
            return result_text, None
        elif mode == 'decode':
            # Add padding if needed, as standard base64 requires it
            missing_padding = len(text) % 4
            if missing_padding:
                text += '=' * (4 - missing_padding)

            base64_bytes = text.encode(encoding) # Encode input base64 string to bytes
            decoded_bytes = base64.b64decode(base64_bytes)
            result_text = decoded_bytes.decode(encoding) # Decode result bytes back to string
            print("[Base64] Decoded text.")
            return result_text, None
        else:
            return None, "Invalid mode specified."

    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"[Base64] Encoding/Decoding error: {e}")
        return None, f"Encoding/Decoding failed: Text contains characters incompatible with '{encoding}'."
    except base64.binascii.Error as e: # Catch specific Base64 errors (like padding)
         print(f"[Base64] Decoding error: {e}")
         return None, f"Decoding failed: Invalid Base64 input. Check characters and padding."
    except Exception as e:
        print(f"Error during Base64 {mode} operation: {e}")
        import traceback
        traceback.print_exc()
        return None, f"An unexpected error occurred during {mode}ing."