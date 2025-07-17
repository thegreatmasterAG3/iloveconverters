# image_tools/image_to_base64_logic.py
import base64
import io
import mimetypes # To guess MIME type

def bytes_with_line_breaks(data_bytes, line_length=76):
    """Helper to insert line breaks into encoded bytes"""
    encoded_string = base64.b64encode(data_bytes).decode('ascii')
    return '\n'.join(encoded_string[i:i+line_length] for i in range(0, len(encoded_string), line_length))

def convert_image_to_base64(image_file, use_data_uri=True, line_breaks=False):
    """
    Converts an uploaded image file object to a Base64 string.

    Args:
        image_file: A Django UploadedFile object.
        use_data_uri (bool): Prepend the 'data:mime/type;base64,' prefix.
        line_breaks (bool): Add line breaks every 76 characters.

    Returns:
        str: The Base64 encoded string (with optional prefix/formatting), or None on error.
    """
    if not image_file:
        return None

    try:
        image_file.seek(0)
        image_bytes = image_file.read() # Read all bytes from the uploaded file

        # Encode the bytes
        if line_breaks:
            # Use helper if line breaks are needed (this returns a string already)
             base64_string = bytes_with_line_breaks(image_bytes)
        else:
            # Standard encoding, then decode to string
            base64_bytes = base64.b64encode(image_bytes)
            base64_string = base64_bytes.decode('ascii') # Use ascii or utf-8, ascii is typical for b64

        print(f"[IMG->B64 Convert] Encoded {len(image_bytes)} bytes to Base64 string (len: {len(base64_string)})")

        if use_data_uri:
            # Guess MIME type from original filename
            mime_type, _ = mimetypes.guess_type(image_file.name)
            if not mime_type:
                mime_type = 'application/octet-stream' # Default if type unknown
            print(f"[IMG->B64 Convert] Guessed MIME Type: {mime_type}")
            return f"data:{mime_type};base64,{base64_string}"
        else:
            return base64_string

    except Exception as e:
        print(f"Error during Image to Base64 conversion: {e}")
        import traceback
        traceback.print_exc()
        return None