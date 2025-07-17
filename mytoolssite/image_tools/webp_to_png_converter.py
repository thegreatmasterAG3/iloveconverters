# image_tools/webp_to_png_converter.py
import io
import os
from PIL import Image

def convert_webp_to_png(webp_file):
    """
    Converts an uploaded WebP file object to PNG format.

    Args:
        webp_file: A Django UploadedFile object (validated as WebP).

    Returns:
        tuple: (bytes: PNG content or None,
                str: output filename or None,
                str: error message or None) <--- NOW ALWAYS 3 VALUES
    """
    if not webp_file:
        return None, None, "No WebP file provided." # Return 3 values

    img = None
    try:
        webp_file.seek(0)
        img = Image.open(webp_file)
        print(f"[WebP->PNG Convert] Opened {webp_file.name}, mode: {img.mode}")

        png_buffer = io.BytesIO()
        save_kwargs = {"format": "PNG", "optimize": True}
        print(f"[WebP->PNG Convert] Saving with options: {save_kwargs}")
        img.save(png_buffer, **save_kwargs)
        print("[WebP->PNG Convert] Saved to buffer.")

        base_name = os.path.splitext(webp_file.name)[0]
        output_filename = f"{base_name}_converted.png"

        png_buffer.seek(0)
        print(f"[WebP->PNG Success] Output filename: {output_filename}")
        # --- FIX: Return 3 values on success ---
        return png_buffer.getvalue(), output_filename, None # Add None for error message
        # --- END FIX ---

    except Exception as e:
        # Catch specific Pillow error if format is not supported
        error_msg = f"An error occurred during conversion: {e}"
        if "cannot identify image file" in str(e) or "decoder webp not available" in str(e):
             print(f"Error: WebP format possibly not supported by Pillow installation or invalid file: {e}")
             error_msg = "Cannot process WebP file. Ensure it's valid and WebP support is installed."
        else:
            print(f"Error during WebP to PNG conversion: {e}")
            import traceback
            traceback.print_exc()

        # --- FIX: Return 3 values on error ---
        return None, None, error_msg
        # --- END FIX ---

    finally:
        if img:
            try: img.close()
            except Exception: pass
        print("[WebP->PNG Cleanup] Closed image object.")