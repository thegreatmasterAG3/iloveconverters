# utility_tools/qr_code_logic.py
import io
# Removed: import qrcode (will import inside try)
from PIL import Image
import base64 # Needed for potential session storage in view, but not directly here now
import mimetypes

# Moved constants inside or keep global if preferred
SIZE_PRESETS = { "S": {"box_size": 6, "border": 2}, "M": {"box_size": 10, "border": 4}, "L": {"box_size": 15, "border": 4} }
ERROR_CORRECTION_MAP = {} # Initialize here

def generate_qr_code(data, error_correction='M', size_preset='M', output_format='PNG'):
    """
    Generates a QR code image from text data.
    """
    if not data:
        return None, None, "Input data cannot be empty."

    # Import necessary parts inside try block
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
        # Update MAP here, after constants are imported
        ERROR_CORRECTION_MAP.update({ "L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H })

        size_params = SIZE_PRESETS.get(size_preset, SIZE_PRESETS['M'])
        error_level = ERROR_CORRECTION_MAP.get(error_correction, ERROR_CORRECT_M)

        output_buffer = io.BytesIO()
        output_filename = "qrcode.png"

        print(f"[QR Generate] Data length: {len(data)}, EC Level: {error_correction}, Size: {size_preset}, Format: {output_format}")

        qr = qrcode.QRCode(
            version=None,
            error_correction=error_level,
            box_size=size_params["box_size"],
            border=size_params["border"],
        )
        qr.add_data(data)
        qr.make(fit=True)

        if output_format.upper() == 'SVG':
            try:
                import qrcode.image.svg # Try importing SVG factory
                factory = qrcode.image.svg.SvgPathImage
                img = qr.make_image(image_factory=factory)
                img.save(output_buffer)
                output_filename = "qrcode.svg"
                print("[QR Generate] Saved as SVG.")
            except ImportError:
                 print("[QR Generate] Error: SVG support requires 'qrcode[pil]' or necessary SVG libraries.")
                 return None, None, "Server error: Could not generate SVG format."

        else: # PNG
            try:
                # Generate PIL image (requires qrcode[pil])
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(output_buffer, format="PNG")
                output_filename = "qrcode.png"
                print("[QR Generate] Saved as PNG.")
            except ImportError:
                 print("[QR Generate] Error: PNG generation requires 'qrcode[pil]' and Pillow.")
                 return None, None, "Server error: Could not generate PNG format."
            except Exception as png_err:
                 print(f"Error saving PNG: {png_err}")
                 raise # Re-raise other Pillow errors

        output_buffer.seek(0)
        return output_buffer.getvalue(), output_filename, None

    # Specific exception for QR data overflow
    except qrcode.exceptions.DataOverflowError:
         print("[QR Generate] Error: Data too long for QR code capacity.")
         return None, None, "Input data is too long for the selected QR code settings. Try lower error correction or less data."
    # Catch general exceptions, including potential ImportError if qrcode isn't installed
    except Exception as e:
        print(f"Error during QR code generation: {e}")
        import traceback
        traceback.print_exc()
        # Check if it was an ImportError specifically
        if isinstance(e, ImportError):
            return None, None, "Server error: Required QR code library is missing."
        return None, None, f"An unexpected error occurred: {e}"