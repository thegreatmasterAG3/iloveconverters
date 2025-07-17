# image_tools/jpg_to_png_converter.py
import io
import os # Need os for filename splitting
from PIL import Image

def convert_jpg_to_png(jpg_file, compression=6, interlace=False):
    """
    Converts an uploaded JPG file object to PNG format with options.

    Args:
        jpg_file: A Django UploadedFile object (validated as JPG).
        compression (int): PNG compression level (0=none, 1=fastest, 9=best/slowest). Default is 6.
        interlace (bool): Whether to save as interlaced PNG.

    Returns:
        tuple: (bytes: PNG content or None, str: output filename or None) on success,
               or (None, None) on error.
    """
    if not jpg_file:
        return None, None

    img = None
    try:
        jpg_file.seek(0)
        img = Image.open(jpg_file)
        print(f"[JPG->PNG Convert] Opened {jpg_file.name}, mode: {img.mode}")

        # Determine if we need to convert mode (e.g., Grayscale JPG)
        # PNG supports RGB, RGBA, L (grayscale), LA (grayscale+alpha), P (palette)
        # If the source JPG is grayscale (L), we can save as grayscale PNG (L)
        # If the source JPG is RGB, save as RGB PNG.
        # Pillow generally handles this well during save if format supports the mode.

        # Save to an in-memory buffer as PNG
        png_buffer = io.BytesIO()

        # Prepare save options
        save_kwargs = {
            "format": "PNG",
            "optimize": True, # Good default
            "compress_level": compression, # Use the provided level
            "interlace": interlace # Use the provided interlace option
        }

        print(f"[JPG->PNG Convert] Saving with options: {save_kwargs}")
        img.save(png_buffer, **save_kwargs)
        print("[JPG->PNG Convert] Saved to buffer.")

        # Construct output filename
        base_name = os.path.splitext(jpg_file.name)[0]
        output_filename = f"{base_name}_converted.png"

        png_buffer.seek(0)
        print(f"[JPG->PNG Success] Output filename: {output_filename}")
        return png_buffer.getvalue(), output_filename

    except Exception as e:
        print(f"Error during JPG to PNG conversion: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        if img:
            try: img.close()
            except Exception: pass
        print("[JPG->PNG Cleanup] Closed image object.")